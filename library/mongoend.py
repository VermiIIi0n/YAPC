"""Async-MongoDB Backend Library for Pixiv"""
from __future__ import annotations
from . import prototypes as proto
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Type, TypeVar, Generic, TypeAlias
from utils import merge_ancestors, sync_await, gen_table
from motor.motor_asyncio import AsyncIOMotorClient as Client
from motor.motor_asyncio import AsyncIOMotorDatabase as DB
from motor.motor_asyncio import AsyncIOMotorCollection as MColl
from bson.tz_util import utc

ItemVar = TypeVar("ItemVar", bound="Item")

proper_setter = proto.proper_setter
CreatorRef: TypeAlias = proto.CreatorRef
Source: TypeAlias = proto.Source
Alias: TypeAlias = proto.Alias
Email: TypeAlias = proto.Email
OrderedItem: TypeAlias = proto.OrderedItem
FrameInfo: TypeAlias = proto.FrameInfo
Dimensions: TypeAlias = proto.Dimensions
Geo: TypeAlias = proto.Geo
Pixiv: TypeAlias = proto.Pixiv
DBRef: TypeAlias = proto.DBRef
UID: TypeAlias = proto.UID


class Item(proto._RichItem):
    def __init__(self, shelf: Shelf):
        self._shelf = shelf

    async def retrieve(self):
        """Retrieve the data from database and update"""
        self.raw = self._proto(**(await self._shelf._get_raw(self._id))).raw

    async def flush(self):
        """Flush the data to database"""
        await self._shelf.upsert(self)

    def update_modified(self):
        """Update the modified timestamp"""
        self.last_modified = datetime.now(tz=utc)

    def as_dbref(self) -> DBRef:
        """Return a DBRef object"""
        if isinstance(self, proto.Tag):
            return DBRef("Tags", self._id)
        if isinstance(self, proto.Creator):
            return DBRef("Creators", self._id)
        if isinstance(self, proto.Picture):
            return DBRef("Pictures", self._id)
        if isinstance(self, proto.Album):
            return DBRef("Albums", self._id)
        if isinstance(self, proto.Collection):
            return DBRef("Collections", self._id)
        if isinstance(self, proto.Binary):
            return DBRef("Binaries", self._id)
        raise TypeError(f"Invalid type for member {type(self)}")


class Picture(Item, proto.Picture):
    """### Picture Class
    * `title`
    * `type` Type of the picture
    * `creator` Creator referrence of the picture
    * `_id` UID
    * `caption` Caption of the picture
    * `sauce` Source of the picture
    * `rating` Rating of the picture
    * `created_time` Time of being created
    * `pixiv` Pixiv info, if any
    * `frame_info` Frame info, if any
    * `src` List of the sources of the picture
    * `Dimensions` Dimensions of the picture
    * `geo` Geo location of the picture
    """
    types: TypeAlias = proto.Picture.types

    def __init__(self, lib: Library, title: str, type: types | int,
                 creator: CreatorRef, _id: UID, caption: str = '', sauce: str = '',
                 rating: float = 3.0, albums: list[proto.UID] = None, created_time: datetime = None,
                 pixiv: Pixiv = None, archived: bool = False, frame_info: FrameInfo = None,
                 src: list[Source] = None, dims: Dimensions = None, geo: Geo = None,
                 saved_time: datetime = None, last_modified: datetime = None,
                 ancestors: list[list[proto.UID]] = None, tags: list[str] = None
                 ):
        Item.__init__(self, lib.Pictures)
        proto.Picture.__init__(self,
                               title=title, type=type, creator=creator, _id=_id, caption=caption,
                               sauce=sauce, rating=rating, albums=albums, created_time=created_time,
                               pixiv=pixiv, tags=tags, archived=archived, frame_info=frame_info,
                               src=src, dims=dims, geo=geo, saved_time=saved_time,
                               last_modified=last_modified, ancestors=ancestors)
        self._proto = proto.Picture

    async def bind_creator(self, creator: Creator, role: str = None, label: str = None):
        if self.creator.id is not None:
            raise ValueError("Creator already bound")
        self.creator = CreatorRef(name=creator.name, id=creator._id,
                                  role=role, label=label)
        ref = DBRef("Pictures", self._id)
        if ref in creator.works:
            return
        await creator.flush()  # Make sure creator is in database
        await self.flush()  # Make sure picture is in database
        # Using transaction to ensure atomicity
        async with await self._shelf.lib.cli.start_session() as sess, sess.start_transaction():
            await creator._shelf._table.update_one(
                {"_id": creator._id},
                {"$push": {"works": ref},  # Using push to avoid overwrite
                 "$set": {"last_modified": datetime.now(utc)}},
                session=sess                # other `bind_creator` calls.
            )
            await self._shelf._table.update_one(
                {"_id": self._id},
                {"$set": {"creator": self.creator.raw,
                          "last_modified": datetime.now(utc)}},
                session=sess
            )
        await creator.retrieve()
        await self.retrieve()

    async def join_album(self, album: Album):
        await self.flush()
        await album.flush()
        async with await self._shelf.lib.cli.start_session() as sess:
            pic_table = self._shelf._table
            al_table = album._shelf._table
            async with sess.start_transaction():
                if album._id not in self.albums:
                    await pic_table.update_one(
                        {"_id": self._id},
                        {"$push": {"albums": album._id},
                         "$set": {"last_modified": datetime.now(utc)}},
                        session=sess
                    )
                if self._id not in album.members:
                    await al_table.update_one(
                        {"_id": album._id},
                        {"$push": {"members": self._id},
                         "$set": {"last_modified": datetime.now(utc)}},
                        session=sess
                    )
                if self.creator.id is None:
                    if self.creator.name not in [c.name for c in album.creators]:
                        await al_table.update_one(
                            {"_id": album._id},
                            {"$push": {"creators": self.creator.raw, },
                             "$set": {"last_modified": datetime.now(utc)}},
                            session=sess
                        )
                elif self.creator.id not in [a.id for a in album.creators]:
                    await al_table.update_one(
                        {"_id": album._id},
                        {"$push": {"creators": self.creator.raw, },
                         "$set": {"last_modified": datetime.now(utc)}},
                        session=sess
                    )
        await self.retrieve()
        await album.retrieve()


class Tag(Item, proto.Tag):
    """### Tag Class
    * `name` A unique name
    * `_id` UID
    * `aliases` List of aliases
    * `desc` Description
    * `members` List of DBRefs of members
    """

    def __init__(self, lib: Library, name: str, _id: UID, aliases: list[Alias] = None,
                 desc: str = '', members: list[DBRef] = None, archived: bool = False,
                 saved_time: datetime = None, last_modified: datetime = None,
                 ancestors: list[list[proto.UID]] = None, cover: proto.Source = None
                 ):
        Item.__init__(self, lib.Tags)
        proto.Tag.__init__(self, name=name, _id=_id, aliases=aliases, desc=desc,
                           members=members, archived=archived, saved_time=saved_time,
                           last_modified=last_modified, ancestors=ancestors, cover=cover)
        self._proto = proto.Tag

    async def add_member(self, member: Item):
        if isinstance(member, proto.Tag):
            raise ValueError("Cannot add tag as member")
        await self.flush()
        await member.flush()
        ref = member.as_dbref()
        async with await self._shelf.lib.cli.start_session() as sess:
            tag_table = self._shelf._table
            other_table = member._shelf._table
            async with sess.start_transaction():
                if ref not in self.members:
                    await tag_table.update_one(
                        {"_id": self._id},
                        {"$push": {"members": ref},
                         "$set": {"last_modified": datetime.now(utc)}},
                        session=sess
                    )
                if self.name not in member.tags:
                    await other_table.update_one(
                        {"_id": member._id},
                        {"$push": {"tags": self.name},
                         "$set": {"last_modified": datetime.now(utc)}},
                        session=sess
                    )
        await self.retrieve()
        await member.retrieve()

    async def remove_member(self, member: Item):
        await self.flush()
        await member.flush()
        ref = member.as_dbref()
        async with await self._shelf.lib.cli.start_session() as sess:
            tag_table = self._shelf._table
            other_table = member._shelf._table
            async with sess.start_transaction():
                if ref in self.members:
                    await tag_table.update_one(
                        {"_id": self._id},
                        {"$pull": {"members": ref},
                         "$set": {"last_modified": datetime.now(utc)}},
                        session=sess
                    )
                if self.name in member.tags:
                    await other_table.update_one(
                        {"_id": member._id},
                        {"$pull": {"tags": self.name},
                         "$set": {"last_modified": datetime.now(utc)}},
                        session=sess
                    )
        await self.retrieve()
        await member.retrieve()


class Creator(Item, proto.Creator):
    """### Creator Class
    * `name` Name
    * `_id` UID
    * `avatar` Profile picture, a Source object
    * `platform` Platform
    * `user_id` User ID of the platform
    * `homepage` Homepage of the platform, if any
    * `primary` Primary creator info, if any
    * `sub_identities` List of CreatorRefs
    * `emails` List of emails
    * `rating` Rating of the creator
    * `gender` Gender info, if any, otherwise ''
    * `desc` Description
    * `birth` Birth info, if any
    * `death` Death info, if any
    * `works` List of work DBRefs
    """

    def __init__(
        self, lib: Library, name: str, _id: UID, avatar: Source = None, platform: str = '',
        user_id: str = '', homepage: str = '', primary: UID = None, gender: str = '',
        sub_identities: list[CreatorRef] = None, emails: list[str] = None,
        rating: float = 3.0, desc: str = '', birth: datetime = None, pixiv: Pixiv = None,
        death: datetime = None, works: list[DBRef] = None, archived: bool = False,
        saved_time: datetime = None, last_modified: datetime = None,
        ancestors: list[list[proto.UID]] = None, tags: list[str] = None
    ):
        Item.__init__(self, lib.Creators)
        proto.Creator.__init__(self, name=name, _id=_id, avatar=avatar, platform=platform,
                               user_id=user_id, homepage=homepage, primary=primary, gender=gender,
                               sub_identities=sub_identities, emails=emails, rating=rating, desc=desc,
                               birth=birth, pixiv=pixiv, death=death, works=works, archived=archived,
                               saved_time=saved_time, last_modified=last_modified, ancestors=ancestors,
                               tags=tags)
        self._proto = proto.Creator


class Album(Item, proto.Album):
    """### Album Class
    * `title` Title
    * `type` Album type
    * `_id` UID
    * `creators` List of CreatorRefs
    * `cover` Cover of the album, a Source object
    * `desc` Description
    * `rating` Rating of the album
    * `pixiv` Pixiv info, if any
    * `members` List of IDs of members
    * `created_time` Creation time
    """
    types: TypeAlias = proto.Album.types

    def __init__(
        self, lib: Library, title: str, type: types | int, creators: list[CreatorRef],
        _id: UID, cover: Source = None, desc: str = '', rating: float = 3.0,
        pixiv: Pixiv = None, members: list[proto.UID] = None, created_time: datetime = None,
        saved_time: datetime = None, last_modified: datetime = None,
        ancestors: list[list[proto.UID]] = None, tags: list[str] = None, archived: bool = False
    ):
        Item.__init__(self, lib.Albums)
        proto.Album.__init__(self, title=title, type=type, creators=creators, _id=_id,
                             cover=cover, desc=desc, rating=rating, pixiv=pixiv, members=members,
                             created_time=created_time, saved_time=saved_time, last_modified=last_modified,
                             ancestors=ancestors, tags=tags, archived=archived)
        self._proto = proto.Album

    async def add_creator(self, creator: Creator, role: str = None, label: str = None):
        creatorref = CreatorRef(
            name=creator.name, id=creator._id, role=role, label=label)
        ref = DBRef("Albums", self._id)
        await creator.flush()  # Make sure creator is in database
        await self.flush()  # Make sure album is in database
        # Using transaction to ensure atomicity
        async with await self._shelf.lib.cli.start_session() as sess, sess.start_transaction():
            if ref not in creator.works:
                await creator._shelf._table.update_one(
                    {"_id": creator._id},
                    {"$push": {"works": ref},  # Using push to avoid overwrite
                     "$set": {"last_modified": datetime.now(utc)}},
                    session=sess                # other `bind_creator` calls.
                )
            if creatorref not in self.creators:
                await self._shelf._table.update_one(
                    {"_id": self._id},
                    {"$push": {"creators": creatorref},
                     "$set": {"last_modified": datetime.now(utc)}},
                    session=sess
                )
        await creator.retrieve()
        await self.retrieve()


class Binary(Item, proto.Binary):
    """### Binary Class
    * `name` Name
    * `type` Binary type
    * `_id` UID
    * `desc` Description
    * `created_time` Creation time
    * `value` Bytes
    * `refs` List of DBRefs of who references this binary
    * `md5` MD5 hash
    """
    types: TypeAlias = proto.Binary.types

    def __init__(
        self, lib: Library, name: str, type: proto.Binary.types | int, value: bytes,
        _id: UID, desc: str = '', created_time: datetime = None, refs: list[DBRef] = None, md5: str = '',
        saved_time: datetime = None, last_modified: datetime = None,
        ancestors: list[list[proto.UID]] = None, tags: list[str] = None, archived: bool = False
    ):
        Item.__init__(self, lib.Binaries)
        proto.Binary.__init__(self, name=name, type=type, value=value, _id=_id, desc=desc,
                              created_time=created_time, refs=refs, md5=md5, saved_time=saved_time,
                              last_modified=last_modified, ancestors=ancestors, tags=tags, archived=archived)
        self._proto = proto.Binary

    async def ref_from(self, item: Item, session=None) -> proto.UID:
        """Reference this binary from an item, will not flush item"""
        ref = item.as_dbref()
        await self.flush()
        if ref not in self.refs:
            await self._shelf._table.update_one(
                {"_id": self._id},
                {"$push": {"refs": ref},
                 "$set": {"last_modified": datetime.now(utc)}},
                session=session
            )
            self.refs.append(ref)
        return self._id


class Collection(Item, proto.Collection):
    types: TypeAlias = proto.Collection.types

    def __init__(
        self, lib: Library, name: str, type: types | int, _id: UID, cover: Source = None, desc: str = '',
        members: list[DBRef] = None, created_time: datetime = None, saved_time: datetime = None,
        last_modified: datetime = None, ancestors: list[list[proto.UID]] = None,
        tags: list[str] = None, archived: bool = False
    ):
        proto.Collection.__init__(self, name=name, type=type, _id=_id, cover=cover, desc=desc,
                                  members=members, created_time=created_time, saved_time=saved_time,
                                  last_modified=last_modified, ancestors=ancestors, tags=tags, archived=archived)
        Item.__init__(self, lib.Collections)
        self._proto = proto.Collection

    async def add_member(self, member: Item):
        ref = member.as_dbref()
        await self.flush()
        await member.flush()
        async with await self._shelf.lib.cli.start_session() as sess, sess.start_transaction():
            if isinstance(member, proto.Collection):
                for parent_chain in self.ancestors:
                    if member._id in parent_chain:
                        raise ValueError("Recurssion detected " +
                                         f"in collection {self._id} and {member._id}")
            if ref not in self.members:
                await self._shelf._table.update_one(
                    {"_id": self._id},
                    {"$push": {"members": ref},
                     "$set": {"last_modified": datetime.now(utc)}},
                    session=sess
                )
            for parent_chain in member.ancestors:
                if parent_chain[-1] == self._id:  # already is direct parent
                    return
            await member._shelf._table.update_one(
                {"_id": member._id},
                {"$push": {"ancestors": {"$each": [
                    parent_chain + [self._id]
                    for parent_chain in merge_ancestors(self.ancestors)
                ]}}}
            )
        await self.retrieve()
        await member.retrieve()


class Trash(Item, proto.Trash):
    def __init__(self, lib: Library, ref: DBRef, birth: datetime,
                 death: datetime, value: dict):
        proto.Trash.__init__(self, ref=ref, birth=birth,
                             death=death, value=value)
        Item.__init__(self, lib.Trashbin)
        self._proto = proto.Trash


class Library(proto.Library):
    """### Async-TinyDB Backend Library
    A simplified wrapper for :class:`asynctinydb.TinyDB` that adds support for
    extended json types.
    """

    def __init__(self, path: str, database: str = '', **kw):
        kw["retryWrites"] = True
        kw["retryReads"] = True
        kw["tz_aware"] = True
        self._cli: Client = Client(path, **kw)
        self._db = self._cli.get_default_database(
            default=database or "Library")

        self._shelfs: dict[str, Shelf] = {
            "Pictures": Shelf(self._db, "Pictures", Picture, self),
            "Creators": CreatorShelf(self._db, self),
            "Tags": TagShelf(self._db, self),
            "Albums": AlbumShelf(self._db, self),
            "Binaries": Shelf(self._db, "Binaries", Binary, self),
            "Collections": Shelf(self._db, "Collections", Collection, self),
            "Trashbin": Trashbin(self._db, self),
        }

    @property
    def cli(self) -> Client:
        return self._cli

    # Using properties for type hints
    @property
    def Pictures(self) -> Shelf[Picture]:
        return self._shelfs["Pictures"]

    @property
    def Creators(self) -> CreatorShelf:
        return self._shelfs["Creators"]  # type: ignore

    @property
    def Tags(self) -> TagShelf:
        return self._shelfs["Tags"]  # type: ignore

    @property
    def Albums(self) -> AlbumShelf:
        return self._shelfs["Albums"]  # type: ignore

    @property
    def Binaries(self) -> Shelf[Binary]:
        return self._shelfs["Binaries"]

    @property
    def Collections(self) -> Shelf[Collection]:
        return self._shelfs["Collections"]

    @property
    def Trashbin(self) -> Trashbin:
        return self._shelfs["Trashbin"]  # type: ignore

    def get_shelf(self, name) -> Shelf:
        return self._shelfs[name]

    def __getattr__(self, name) -> Shelf:
        return self.get_shelf(name)

    def __iter__(self):
        return iter(self._shelfs.values())

    async def close(self):
        for shelf in self._shelfs.values():
            await shelf.close()
        self.cli.close()

    def __repr__(self):
        return gen_table(("MongoDB Backend Library",
                          f"Path: {self._cli.address}",
                          f"Pictures: {len(self.Pictures)}",
                          f"Creators: {len(self.Creators)}",
                          f"Tags: {len(self.Tags)}",
                          f"Albums: {len(self.Albums)}",
                          f"Binaries: {len(self.Binaries)}",
                          f"Collections: {len(self.Collections)}",
                          f"Trashbin: {len(self.Trashbin)}"))


class Shelf(proto.Shelf, Generic[ItemVar]):
    """### Async-TinyDB Backend Shelf
    A simplified wrapper for :class:`asynctinydb.TinyDB` that adds support for
    extended json types.
    """

    def __init__(self, db: DB, name: str, type: Type[ItemVar], lib: Library):
        self._db = db
        self._name = name
        self._table: MColl = db.get_collection(name)
        self._cache: dict[proto.UID, ItemVar] = {}
        self._type = type
        self._lib = lib

    @property
    def name(self):
        return self._name

    @property
    def lib(self):
        return self._lib

    async def get(self, _id: UID) -> ItemVar:
        if _id in self._cache:
            return self._cache[_id]
        ret: dict[str, Any] = await self._get_raw(_id)
        self._cache[_id] = self._type(self.lib, **ret)
        return self._cache[_id]

    async def _get_raw(self, _id: UID) -> dict[str, Any]:
        ret: dict[str, Any] | None = await self._table.find_one({"_id": _id})
        if ret is None:
            raise KeyError(_id)
        return ret

    async def contains(self, _id: UID) -> bool:
        return await self._table.find_one({"_id": _id}) is not None

    async def upsert(self, doc: ItemVar) -> list[UID]:
        ret = await self._table.find_one_and_update({"_id": doc._id}, {"$set": doc}, upsert=True)
        self._cache[doc._id] = doc
        return ret

    async def delete(self, _id: UID) -> ItemVar:
        item = await self.get(_id)
        await self.lib.Trashbin.throw(item)
        deleted = await self._table.find_one_and_delete({"_id": _id},)
        self._cache.pop(_id, None)
        return deleted

    def __len__(self):
        return sync_await(self._table.count_documents({}))

    def __aiter__(self) -> AsyncIterator[ItemVar]:
        async def iteror():
            async for raw in self._table.find({}, {"_id": 1}):
                yield await self.get(raw["_id"])
        return iteror()

    def _aiter_raw(self):
        return self._table.find({}).__aiter__()

    async def new_uid(self) -> UID:
        new = UID()
        while await self.contains(new):
            new = UID()
        return new

    async def close(self):
        for item in self._cache.values():
            await item.flush()


class AlbumShelf(Shelf[Album], proto.AlbumShelf):
    def __init__(self, db: DB, lib: Library):
        super().__init__(db, "Albums", Album, lib)
        self._pid_cache: dict[int, UID] | None = None

    async def get_by_pid(self, pid: int) -> Album | None:
        if self._pid_cache is None:
            await self._build_pid_cache()
        assert self._pid_cache is not None
        if pid not in self._pid_cache:
            return None
        return await self.get(self._pid_cache[pid])

    async def pid_to_id(self, pid: int) -> UID | None:
        if self._pid_cache is None:
            await self._build_pid_cache()
        assert self._pid_cache is not None
        return self._pid_cache.get(pid, None)

    async def _build_pid_cache(self):
        self._pid_cache = {i["pixiv"]["pid"]: i["_id"] async for i in
                           self._table.find({"pixiv.pid": {"$exists": True}},
                                            projection={"pixiv.pid": 1})}

    async def upsert(self, doc: Album) -> list[UID]:
        if self._pid_cache is None:
            await self._build_pid_cache()
        if "pixiv" in doc:
            assert self._pid_cache is not None
            self._pid_cache[doc.pixiv.pid] = UID(doc._id)
        return await super().upsert(doc)

    async def delete(self, _id: UID) -> Album:
        if self._pid_cache is None:
            await self._build_pid_cache()
        assert self._pid_cache is not None
        pic = await self.get(_id)
        if "pixiv" in pic:
            self._pid_cache.pop(pic.pixiv.pid, None)
        return await super().delete(_id)


class CreatorShelf(Shelf[Creator], proto.CreatorShelf):
    def __init__(self, db: DB, lib: Library):
        super().__init__(db, "Creators", Creator, lib)
        self._uid_cache: dict[int, UID] | None = None

    async def get_by_uid(self, uid: int) -> Creator | None:
        if self._uid_cache is None:
            await self._build_uid_cache()
        assert self._uid_cache is not None
        if uid not in self._uid_cache:
            return None
        return await self.get(self._uid_cache[uid])

    async def uid_to_id(self, uid: int) -> UID | None:
        if self._uid_cache is None:
            await self._build_uid_cache()
        assert self._uid_cache is not None
        return self._uid_cache.get(uid, None)

    async def _build_uid_cache(self):
        self._uid_cache = {i["pixiv"]["uid"]: i["_id"] async for i in
                           self._table.find({"pixiv.uid": {"$exists": True}},
                                            projection={"pixiv.uid": 1})}

    async def upsert(self, doc: Creator) -> list[UID]:
        if self._uid_cache is None:
            await self._build_uid_cache()
        if "pixiv" in doc:
            assert self._uid_cache is not None
            self._uid_cache[doc.pixiv.uid] = UID(doc._id)
        return await super().upsert(doc)

    async def delete(self, _id: UID) -> Creator:
        if self._uid_cache is None:
            await self._build_uid_cache()
        assert self._uid_cache is not None
        creator = await self.get(_id)
        if "pixiv" in creator:
            self._uid_cache.pop(creator.pixiv.uid, None)
        return await super().delete(_id)


class TagShelf(Shelf[Tag], proto.TagShelf):
    def __init__(self, db: DB, lib: Library):
        super().__init__(db, "Tags", Tag, lib)
        self._name_cache: dict[str, UID] | None = None

    async def get_by_name(self, name: str) -> Tag | None:
        if self._name_cache is None:
            await self._build_name_cache()
        assert self._name_cache is not None
        if name not in self._name_cache:
            return None
        return await self.get(self._name_cache[name])

    async def name_to_id(self, name: str) -> UID | None:
        if self._name_cache is None:
            await self._build_name_cache()
        assert self._name_cache is not None
        return self._name_cache.get(name, None)

    async def _build_name_cache(self):
        self._name_cache = {i["name"]: i["_id"] async for i in
                            self._table.find({}, projection={"name": 1})}

    async def upsert(self, doc: Tag) -> list[UID]:
        if self._name_cache is None:
            await self._build_name_cache()
        assert self._name_cache is not None
        self._name_cache[doc.name] = UID(doc._id)
        return await super().upsert(doc)

    async def delete(self, _id: UID) -> Tag:
        if self._name_cache is None:
            await self._build_name_cache()
        assert self._name_cache is not None
        tag = await self.get(_id)
        self._name_cache.pop(tag.name, None)
        return await super().delete(_id)


class Trashbin(Shelf[Trash]):
    def __init__(self, db: DB, lib: Library):
        super().__init__(db, "Trashbin", Trash, lib)

    async def throw(self, item: Item, ttl: timedelta = timedelta(days=30)) -> Trash:
        """Throw an item into trashbin, and delete it after ttl"""
        ref = DBRef(item._shelf.name, item._id)
        birth = datetime.now(tz=utc)
        death = birth + ttl
        value = item.raw.copy()
        trash = Trash(self.lib, ref=ref, birth=birth, death=death, value=value)
        await trash.flush()
        return trash

    async def clear(self):
        """Clear dead trashes"""
        execs = [i["_id"] for i in await self._table.search({},
                                                            {"death": 1}) if i.death >= datetime.now(tz=utc)]
        await self._table.delete_many({"_id": {"$in": execs}})
