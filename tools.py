"""### Toolbox for database
* `migrate` - Migrate your data from one database to another.
* `check` - Check your database for errors.
* `repair` - Repair your database.
"""

import os
import argparse
import asyncio
import types
from library import tinyend as tn, mongoend as mg, prototypes as pt
from utils import merge_ancestors, real_path, ObjDict
from typing import Any, Awaitable, Callable, Coroutine

err_map = {
    100: "Schema Violation",
    101: "Field Type Mismatch",
    102: "Unreasonable Value",
    200: "Recursive Ancestors Referrence",
    201: "Ancestor Not Found",
    202: "Ancestors Chain Not minimal",
    204: "Creator Not Found",
    205: "Creators Duplication",
    206: "Creators Name Duplication",
    207: "Invalid DBRef",
    208: "One Way Referrence",
    209: "Tag Not Found",
    210: "Tag Names Duplication",
    211: "Picture Not Found",
    212: "Datetime Error",
    213: "Trash Overdue",
    214: "Binary Not Found",
    215: "Invalid Filename",
    300: "Orphan Document",
}


async def migrate(args: argparse.Namespace):
    """### Migration Tool
    Migrate your data from one database to another.
    """
    if not args.to:
        print("Please specify the destination database.")
        exit(1)

    if args.to == args.database:
        print("Please specify a different destination database.")
        exit(1)

    # Determine DB types
    if args.database.lower().startswith("mongodb"):
        ft: types.ModuleType = mg
        libf: tn.Library | mg.Library = mg.Library(args.database)
    elif args.database.lower().endswith(".json"):
        ft = tn
        libf = tn.Library(args.database,
                          indent=args.indent, ensure_ascii=args.ensure_ascii)
    else:
        print("Unknown database type.")
        exit(1)

    if args.to.lower().startswith("mongodb"):
        tt: types.ModuleType = mg
        libt: tn.Library | mg.Library = mg.Library(args.to)
    elif args.to.lower().endswith(".json"):
        if os.path.exists(args.to):
            print("Destination database already exists.")
            exit(1)
        tt = tn
        libt = tn.Library(args.to,
                          indent=args.indent, ensure_ascii=args.ensure_ascii)
    else:
        print("Unknown database type.")
        exit(1)

    print(f"Migrating from {args.database} to {args.to}")

    if tt == ft:
        if tt is tn:
            with open(args.database, 'r') as r:
                with open(args.to, 'w') as f:
                    f.write(r.read())
            exit(0)
        if tt is mg:
            ...

    batch = 1024
    ls: list[Awaitable] = []
    count = 0

    name_type_pairs = (
        ("Pictures", tt.Picture),
        ("Albums", tt.Album),
        ("Tags", tt.Tag),
        ("Creators", tt.Creator),
        ("Collections", tt.Collection),
        ("Binaries", tt.Binary),
        ("Trashbin", tt.Trash),
    )

    # Migration
    for name, t in name_type_pairs:
        async for i in libf.get_shelf(name):
            new = t(libt, **i.raw)
            count += 1
            ls.append(new.flush())
            if count % batch == 0:
                await asyncio.gather(*ls)
                ls = []
        await asyncio.gather(*ls)
        ls = []
        count = 0
        libf.get_shelf(name)._cache.clear()

        print(f"Migrated {name}")

    # await libf.close()
    await libt.close()
    print("Migration Complete")


async def check(args: argparse.Namespace, repair: int = 0):
    """### Check Tool
    Check your database for errors.
    """
    import yaml
    config = ObjDict[Any](yaml.safe_load(open(real_path("config.yaml"), 'r')))

    print("Checking Database...")

    def perror(err: int, msg: str):
        if repair:
            print(f"Repairing {err_map[err]}: {msg}")
        elif err not in err_map:
            print(f"Unknown Error Code: {err}")
        elif err not in args.ignore or []:
            print(f"[red]Err: {err} - {err_map[err]}[/red]: {msg}")

    # Determine DB types
    if args.database.lower().startswith("mongodb"):
        db_t: types.ModuleType = mg
        lib: tn.Library | mg.Library = mg.Library(args.database)
    elif args.database.lower().endswith(".json"):
        db_t = tn
        lib = tn.Library(args.database,
                         indent=args.indent, ensure_ascii=args.ensure_ascii)
    else:
        print("Unknown database type.")
        exit(1)

    async def checkDBRef(ref: pt.DBRef, lib: pt.Library):
        try:
            ret = await lib.get_shelf(ref.collection).get(ref.id)
            if ret is None:
                return 207
        except KeyError:
            return 207
        return 0

    async def deep_checkDBRef(data, lib):
        for k, v in data.items():
            if isinstance(v, pt.DBRef):
                ret = await checkDBRef(v, lib)
                if ret:
                    if repair:
                        data.pop(k)
                    return ret
            elif hasattr(v, "raw"):
                ret = await deep_checkDBRef(v, lib)
                if ret:
                    return ret

    async def checkCreator(creator: pt.CreatorRef, lib: pt.Library):
        if creator.name is None:
            return 204
        if await lib.Creators.get(creator.id) is None:
            return 201
        return 0

    async def checkCreators(creators: list[pt.CreatorRef], lib: pt.Library):
        if len(creators) == 0:
            return 204
        if len(creators) != len(set(creators)):
            return 205
        if len(set(i.name for i in creators)) != len(creators):
            return 206
        return 0

    async def checkTags(tags: list[str], lib: pt.Library):
        if len(tags) != len(set(tags)):
            return 210
        for tag in tags:
            if await lib.Tags.get_by_name(tag) is None:
                return 209
        return 0

    async def checkAncestors(ancestors: list[list[pt.UID]], lib: pt.Library):
        if len(ancestors) == 0:
            return 0
        for chain in ancestors:
            if len(set(chain)) != len(chain):
                return 200
            for uid in chain:
                if await lib.Collections.get(uid) is None:
                    return 201
        if len(ancestors) != len(merge_ancestors(ancestors)):
            return 202
        return 0

    async def checkSource(source: pt.Source, lib: pt.Library):
        if source.type not in config.source_types:
            return 102
        if source.type == source.types.url:
            assert isinstance(source.value, str)
            if not source.value.startswith("http"):
                return 102
        elif source.type == source.types.filename:
            assert isinstance(source.value, str)
        elif source.type == source.types.bin:
            assert isinstance(source.value, pt.UID)
            if await lib.Binaries.get(source.value) is None:
                return 214
        return 0

    async def repairTags(item, err):
        if err == 209:
            item.tags = [tag for tag in item.tags if await lib.Tags.get_by_name(tag) is not None]
        elif err == 210:
            item.tags = list(set(item.tags))

    async def repairAncestors(item, err):
        if err == 201:
            ls: list[list[pt.UID]] = []
            for chain in item.ancestors:
                good = True
                for uid in chain:
                    if await lib.Collections.get(uid) is None:
                        good = False
                        break
                if good:
                    ls.append(chain)
            item.ancestors = ls
        elif err == 202:
            item.ancestors = merge_ancestors(item.ancestors)
    print("Checking Pictures...")
    # Check Pictures
    async for pic_raw in lib.Pictures._aiter_raw():
        try:
            pic = db_t.Picture(lib, **pic_raw)
        except pt.FieldTypeError as e:
            perror(101, f"Invalid Picture: {pic_raw['_id']} - {e}")
            continue
        except TypeError as e:
            perror(100, f"Invalid Picture: {pic_raw['_id']} - {e}")
            continue
        ret = await deep_checkDBRef(pic, lib)
        if ret:
            perror(ret, f"Invalid DBRef in Picture {pic_raw['_id']}")
        if pic.last_modified < pic.created_time:
            perror(
                212, f"Picture {pic._id} last modified time earlier than creation time.")
            if repair:
                pic.last_modified = pic.created_time
        if pic.last_modified < pic.saved_time:
            perror(
                212, f"Picture {pic._id} last modified time earlier than save time.")
            if repair:
                pic.last_modified = pic.saved_time
        if pic.created_time > pic.saved_time:
            perror(
                212, f"Picture {pic._id} creation time later than save time.")
            if repair:
                pic.created_time = pic.saved_time
        for s in [s.value for s in pic.src if s.type == "filename"]:
            if not os.path.exists(os.path.join(config.puller.path, s)):
                perror(
                    213, f"Picture {pic._id} source file {s} does not exist.")
        ret = await checkCreator(pic.creator, lib)
        if ret:
            perror(ret, f"Picture {pic._id} creator error.")
            if ret == 201 and repair:
                pic.creator.id = None
        ret = await checkTags(pic.tags, lib)
        if ret:
            perror(ret, f"Picture {pic._id} tag error.")
            if repair:
                await repairTags(pic, ret)
        ret = await checkAncestors(pic.ancestors, lib)
        if ret:
            perror(ret, f"Picture {pic._id} ancestor error.")
            if repair:
                await repairAncestors(pic, ret)
        if repair:
            await pic.flush()

    print("Other Checks have not been implemented yet.")


async def repair(args: argparse.Namespace):
    """### Repair Tool
    Repair your database.
    """
    await check(args, repair=1)

opts: dict[str, Callable[..., Coroutine]] = {
    "migrate": migrate,
    "check": check,
    "repair": repair,
}

parser = argparse.ArgumentParser(prog="YAPC Toolbox",
                                 formatter_class=argparse.RawTextHelpFormatter,
                                 description="Migrate, check, repair your database")

parser.add_argument("cmd", choices=opts.keys(), help="Command to run\n" +
                    "migrate: Migrate your data from one database to another\n" +
                    "   tools.py migrate from <MongoDB URL/Path to file> to " +
                    "<MongoDB URL/Path to file>\n\n" +
                    "check: Check your database for errors\n" +
                    "   tools.py check <MongoDB URL/Path to file>\n\n\n" +
                    "repair: Repair your database\n" +
                    "   tools.py repair <MongoDB URL/Path to file>\n\n")

parser.add_argument("database", nargs="?", type=str,
                    help="Database to check/repair/migrate from")

parser.add_argument("--to", type=str, help="Target database URL/Path to file")

parser.add_argument("--ignore", type=int, nargs='+',
                    help="List of error codes to be ignored")
parser.add_argument("--indent", type=int, default=2,
                    help="Indentation for JSON files")
parser.add_argument("--ensure_ascii", action="store_true",
                    help="Ensure ASCII for JSON files")

args = parser.parse_args()

asyncio.run(opts[args.cmd](args))
