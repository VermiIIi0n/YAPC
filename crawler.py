"""### Crawler Module"""

from __future__ import annotations
import os
import logging
import asyncio
import json
import pyxiv as px
import httpx
from datetime import datetime
from library import prototypes as proto
from functools import partial
from urllib.parse import unquote_plus as unquote, urlparse
from pullers import AsyncPuller, QueryParamTypes, HeaderTypes
from pullers import CookieTypes, ProxiesTypes
from utils import LoggerLike, EventHook, AsyncActionChain, EventHint
from utils import sync_await, ObjDict, to_ordinal, real_path
from typing import Iterable, Literal, overload, TYPE_CHECKING
from types import ModuleType

if TYPE_CHECKING:
    from library import tinyend as td  # For type hints only
    from library import mongoend as mg  # For type hints only

_jdumps = partial(json.dumps, indent=2, ensure_ascii=False,
                  default=lambda x: '<Not JSON Serializable>')


class Bookmarks:
    """### Bookmarks Class

    A sequence of bookmarks, with a few extra methods.
    """

    def __init__(self, crawler: PixivCrawler, uid: str,
                 private=False, limit=48, tag: str = None):
        """
        * `uid` User ID of this bookmark
        * `limit` Limit of bookmarks per page
        * `private` Private bookmarks
        """
        self.crl = crawler
        self.kw = {
            "uid": uid,
            "limit": limit,
            "rest": ("show", "hide")[private],
            "tag": tag
        }
        self._total: int = None  # type: ignore
        self._cache: dict[int, list] = {}

    async def _build_cache(self, block):
        data = await self.crl.user_illusts_bookmarks(
            offset=block*self.kw["limit"], **self.kw)
        if self._total is None:
            self._total = data.total
        if self._total != data.total:
            raise RuntimeError("Bookmark modified during runtime")
        self._cache[block] = data.works

    async def at(self, index: int):
        block = max(index // self.kw["limit"], 0)
        if block not in self._cache:
            await self._build_cache(block)
        if index >= self._total:
            raise IndexError(f"Index {index} out of range [0-{self._total-1}]")
        return self._cache[block][index % self.kw["limit"]]

    async def slice(self, start: int, stop: int, step: int = 1) -> list[ObjDict]:
        ls: list[ObjDict] = []
        for b in range(start//self.kw["limit"], stop//self.kw["limit"]+1):
            if b not in self._cache:
                await self._build_cache(b)
            ls.extend(self._cache[b])
        return ls[start:stop:step]

    def clear_cache(self):
        self._total = None
        self._cache.clear()

    async def total(self) -> int:
        if self._total is None:
            await self._build_cache(0)
        return self._total

    def __aiter__(self):
        async def iterator():
            for i in range(await self.total()):
                yield await self.at(i)
        return iterator()


class PixivCrawler:
    """Pixiv Crawler class"""

    def __init__(
            self,
            backend: Literal["tinyend", "mongoend"],
            path: str,
            data_path: str,
            cookies: CookieTypes,
            uid: str | int = '',
            headers: HeaderTypes = None,
            proxies: ProxiesTypes = None,
            params: QueryParamTypes = None,
            interval: float = 1.0,
            threads: int = 8,
            timeout: float = 10.0,
            retry: int = 10,
            overwrite: bool = False,
            logger: LoggerLike = None,
            pixiv_host: str = 'https://www.pixiv.net',
            lib_args: dict = None,
            **kw
    ):

        self._logger = logger or logging.getLogger(__name__)
        self.data_path = data_path
        self._host = pixiv_host
        self._logger.info(f"Initializing PixivCrawler with {backend}")
        self._logger.info(f"DB path: {path}\n"+f"data path: {data_path}")

        _headers = httpx.Headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
            "Referer": "https://www.pixiv.net/",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-ch-ua": '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        })
        headers = httpx.Headers(headers)
        _headers.update(headers)

        self._puller = AsyncPuller(
            headers=_headers,
            cookies=cookies,
            proxies=proxies,
            params=params,
            interval=interval,
            max_workers=threads,
            timeout=timeout,
            retry=retry,
            overwrite=overwrite,
            **kw
        )
        self._client = self._puller.client
        self._logger.debug(f"Puller initialized with {self._puller}")
        self.uid = str(uid) or sync_await(self.fetch_uid())
        self._logger.info(f"Target User ID: {self.uid}")

        # Initialise Library Backend
        if backend == "tinyend":
            from library import tinyend
            self._end: ModuleType = tinyend
            self._lib: td.Library|mg.Library = tinyend.Library(
                path=path, **(lib_args or {}))
        elif backend == "mongoend":
            from library import mongoend
            self._end = mongoend
            self._lib = mongoend.Library(path=path, **(lib_args or {}))
        else:
            raise ValueError(f"Invalid backend: {backend}")

        # Initialise Event Hooks
        self._event_hooks = EventHook()
        self._on = EventHint(self._event_hooks)
        self._event_hooks.hook("crawl.work", AsyncActionChain())
        self._event_hooks.hook("finish.work", AsyncActionChain())
        self._event_hooks.hook("deleted.work", AsyncActionChain())
        self._event_hooks.hook("crawl.bookmark", AsyncActionChain())
        self._event_hooks.hook("finish.bookmark", AsyncActionChain())
        self._event_hooks.hook("destroy", AsyncActionChain())

    @property
    def client(self):
        return self._client

    @property
    def puller(self):
        return self._puller

    @property
    def lib(self):
        return self._lib

    @property
    def on(self):
        return self._on

    @property
    def event_hooks(self):
        return self._event_hooks

    async def crawl_bookmarks(self, uid='', start: int = 0, stop: int = None, ascend=False,
                              private=False, tag: str = None, overwrite=False):
        """
        * `stop` is exclusive
        """
        bk = Bookmarks(self, uid or self.uid, private, tag=tag)
        if stop is None:
            stop = await self.x_cmp_bookmarks(bk)
            self._logger.info(f"Detected boundry at offset {stop}")
        else:
            if stop < 0:
                stop = await bk.total() + stop + 1
            self._logger.info(f"Set boundry at offset {stop}")

        self._logger.info("Start crawling bookmarks\n" +
                          f"private: {private}\n" + f"tag: {tag}\n" +
                          f"start: {start} stop: {stop} ascend: {ascend}")
        await self.event_hooks.aemit("crawl.bookmark", self, uid, start,
                                     stop, ascend, private, tag)
        _start, _stop, _step = (
            start, stop, 1) if ascend else (stop-1, start-1, -1)
        for i in range(_start, _stop, _step):
            try:
                illust = await bk.at(i)
            except IndexError:
                self._logger.warning(f"Index {i} out of range, skipped")
                break
            # Deleted work
            if illust.title == "-----":
                self._logger.error(f"Picture {illust.id} is deleted, skipped")
                await self.event_hooks.aemit("deleted.work", self, illust.id)
                continue
            await self.crawl_work(illust.id, overwrite)
            await asyncio.sleep(self._puller.interval)
        await self.event_hooks.aemit("finish.bookmark", self, bk)

    async def crawl_work(self, pid: str | int, overwrite=False):
        pid = int(pid)  # Type of pid in the Library is int...Sorry for that.
        self._logger.info(f"Crawling work {pid}")
        await self.event_hooks.aemit("crawl.work", self, pid)
        a_id = await self._lib.Albums.pid_to_id(pid)
        if a_id:  # If exists
            if not overwrite:
                self._logger.info(f"Skip crawling existing work {pid}")
                return a_id
            self._logger.info(f"Picture {pid} already exists, overwriting")
        else:
            a_id = await self._lib.Albums.new_uid()

        # Get raw data from Pixiv
        w_data = await self.illust(pid)

        # Get creator or create one
        # Same as pid, type of uid in the Library is int
        uid = int(w_data.userId)
        creator = await self._lib.Creators.get_by_uid(uid)
        if creator is None:
            c_id = await self._lib.Creators.new_uid()
            c_data = await self.user(uid)
            creator = await self.construct_creator(c_id, w_data.userAccount, c_data)
            await creator.flush()

        # Get tags or create them
        tags: list[td.Tag] = []
        for t_data in w_data.tags.tags:
            t_name = unquote(t_data.tag)
            tag = await self._lib.Tags.get_by_name(t_name)
            if tag is None:
                assert isinstance(t_data, ObjDict)
                t_id = await self._lib.Tags.new_uid()
                tag = await self.construct_tag(t_id, t_data)
                await tag.flush()
            tags.append(tag)

        # Create work
        assert a_id
        album = await self.construct_album(a_id, w_data)
        await album.add_creator(creator)
        for tag in tags:
            await tag.add_member(album)

        # Create pages
        for p in range(w_data.pageCount):
            _id = await self._lib.Pictures.new_uid()
            picture = await self.construct_picture(_id, p, w_data)
            await picture.join_album(album)
            for tag in tags:
                await tag.add_member(picture)

            # Start pulling files
            files: dict[str, list[str | None]] = {
                "original": [None, None],
                "ugoira": [None, None],
            }  # Stored as [url, filepath]
            for src in picture.src:
                files[src.label][src.type ==
                                 src.types.filename] = str(src.value)
            for url, filename in files.values():
                if url and filename:
                    filepath = real_path(
                        os.path.join(self.data_path, filename))
                    await self.puller.pull(url, filepath, overwrite=overwrite)
        await self.event_hooks.aemit("finish.work", self, pid)
        return album._id

    async def x_cmp_bookmarks(self, bk: Bookmarks, lookback=3, batch=128) -> int:
        """### Cross compare bookmarks with library, 
        return index after last not-in-lib work
        * `lookback` When encountered an existing work, check more works after it, 
        in case it's an accidentally unliked-and-reliked work
        * `offset` Starting offset
        * `private` Private bookmarks
        """
        # binary search
        total = await bk.total()
        offset = 0
        while True:
            pic = await bk.at(offset)  # Get work at the offset

            # First stage, iter through blocks, find the one with old items
            # If not exists
            if not await self._lib.Albums.pid_to_id(int(pic.id)):
                if offset == total-1:  # Non of the works is in the library
                    return total  # Will be the index after the last item

            # Second stage, iter through items in the block to locate the first old item
            else:  # If exists
                found = True  # Boundry found
                # Make sure it's not an unliked-reliked item by checking more items
                for i in range(1, lookback+1):
                    if i+offset >= total:  # In case it reached the end
                        return total
                    pic = await bk.at(offset+i)
                    if not await self._lib.Albums.pid_to_id(int(pic.id)):
                        found = False
                        break  # False Positive
                if found:
                    if not offset:  # Up to date
                        return 0
                    for i in range(1, batch+1):
                        pic = await bk.at(offset-i)
                        if not await self._lib.Albums.pid_to_id(int(pic.id)):
                            return offset-i+1
                    raise RuntimeError("This should not happen")

            # Update offset when not found
            offset = min(offset+batch, total-1)

    async def iter_illust_recommend(self, pid: str):
        """### Iter through all recommended illusts from a given pid"""
        works = await self.illust_recommend(pid)
        next_ids = list(works.nextIds)  # A copy
        while True:
            for i in works.illusts:
                yield i
            if not next_ids:  # All recommendations are consumed
                return
            works = await self.illust_recommend(illust_ids=next_ids[:18])
            next_ids = next_ids[18:]

    async def construct_album(self, _id: proto.UID, data: ObjDict) -> td.Album:
        """### Construct an Album from raw data"""
        self._logger.info(f"Constructing album {data.id}")
        series = data.seriesNavData
        _prev = int(series.prev.id) if series and series.prev else None
        _next = int(series.next.id) if series and series.next else None
        new = self._end.Album(
            lib=self._lib,
            _id=_id,
            title=unquote(data.title),
            type=0,
            creators=[proto.CreatorRef(unquote(data.userName),
                                       await self._lib.Creators.uid_to_id(int(data.userId)))],
            cover=None,
            desc=unquote(data.description),
            pixiv=proto.Pixiv(pid=int(data.id), uid=int(data.userId),
                              type=data.illustType, original=data.isOriginal,
                              prev=_prev, next=_next),
            created_time=datetime.fromisoformat(data.createDate),
        )
        self._logger.info(f"Constructed album {data.id}")
        return new

    async def construct_picture(self, _id: proto.UID, page: int, data: ObjDict) -> td.Picture:
        """### Construct a work from a given data"""
        pid = int(data.id)
        filename_0 = os.path.basename(urlparse(data.urls.original).path)
        filename = filename_0.replace("_p0", f"_p{page}")
        url = data.urls.original.replace(filename_0, filename)
        self._logger.info(f"Constructing work {pid} page {page}")
        series = data.seriesNavData
        _prev = int(series.prev.id) if series and series.prev else None
        _next = int(series.next.id) if series and series.next else None
        new: td.Picture = self._end.Picture(
            lib=self._lib,
            title=unquote(data.title),
            type=data.illustType,
            creator=proto.CreatorRef(unquote(data.userName),
                                     await self._lib.Creators.uid_to_id(int(data.userId))),
            _id=_id,
            caption=unquote(data.description),
            sauce="pixiv",
            rating=3.0,
            albums=[],  # Bind later
            created_time=datetime.fromisoformat(data.createDate),
            pixiv=proto.Pixiv(pid=pid, uid=int(data.userId), type=data.illustType,
                              original=data.isOriginal, prev=_prev, next=_next),
            archived=False,
            src=[
                proto.Source("url", url, "original"),
                proto.Source("filename", filename, "original"),
            ],
            dims=proto.Dimensions(data.width, data.height),
        )
        await self.add_ugoira_meta(new)
        self._logger.info(f"Constructed work {pid} page {page}")
        return new

    async def add_ugoira_meta(self, p: proto.Picture):
        """### Add ugoira meta to a Picture object"""
        if p.pixiv.type != proto.Pixiv.types.ugoira:
            return
        self._logger.info(f"Fetching ugoira meta for {p.pixiv.pid}")
        meta = await self.illust_ugoira_meta(p.pixiv.pid)
        p.frame_info = proto.FrameInfo(
            0, "ugoira", p._id, float(meta.frames[0].delay))
        p.src.append(proto.Source("url", meta.originalSrc, "ugoira"))
        p.src.append(proto.Source("filename",
                                  os.path.basename(
                                      urlparse(meta.originalSrc).path),
                                  "ugoira"))

    async def construct_creator(self, _id: proto.UID, userAccount: str, data: ObjDict) -> td.Creator:
        """### Construct a Creator object from a given user data"""
        uid = int(data.userId)
        name = unquote(data.name)
        self._logger.info(f"Constructing creator {name} ({uid})")
        new = self._end.Creator(
            lib=self._lib,
            name=name,
            _id=_id,
            avatar=proto.Source("url", data.imageBig),
            platform="pixiv",
            user_id=userAccount,
            homepage=f"https://www.pixiv.net/users/{uid}",
            gender=data.gender.name or '',
            sub_identities=[proto.CreatorRef(
                name, None, label=k, url=v) for k, v in (data.social or {}).items()],
            desc=unquote(data.comment),
            pixiv=proto.Pixiv(uid=uid),
        )
        self._logger.info(f"Constructed creator {name} ({uid})")
        return new

    async def construct_tag(self, _id: proto.UID, data: ObjDict) -> td.Tag:
        """### Construct a Tag object from a given tag data"""
        name = unquote(data.tag)
        data.default = None  # Set default value for ObjDict
        aliases = data.translation or ObjDict()
        if data.romaji:
            aliases.romaji = data.romaji
        info = (await self.tag_info(name)) or ObjDict()  # extra info
        info.default = None
        self._logger.info(f"Constructing tag {name}")
        new = self._end.Tag(
            lib=self._lib,
            name=name,
            _id=_id,
            aliases=[proto.Alias(unquote(v), k) for k, v in aliases.items()],
            desc=unquote(info.abstract or ''),
            cover=proto.Source("url", info.thumbnail),
        )
        self._logger.info(f"Constructed tag {name}")
        return new

    async def fetch_uid(self):
        """Fetches the uid of current user"""
        if not getattr(self, "uid", False):
            self.uid = (await self.client.get(self._host)).headers["X-Userid"]
        return self.uid

    async def join(self):
        await self.lib.flush()
        await self.puller.join()

    async def close(self):
        self._logger.info("Closing Pixiv client")
        await self.event_hooks.aemit("destroy", self)
        await self.lib.close()
        await self.puller.join()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    ############################# Low Level APIs #############################

    async def illust(self, pid: str | int) -> ObjDict:
        """Get illust info"""
        pid = str(pid)
        method, url, params = px.illust(pid, host=self._host)
        return await self._request(method, url, params)

    async def illust_pages(self, pid: str | int) -> ObjDict:
        """Get image urls"""
        pid = str(pid)
        method, url, params = px.illust_pages(pid, host=self._host)
        return await self._request(method, url, params)

    async def illust_ugoira_meta(self, pid: str | int):
        """Get ugoira meta"""
        pid = str(pid)
        method, url, params = px.illust_ugoira_meta(pid, host=self._host)
        return await self._request(method, url, params)

    async def illusts_bookmark_add(self, pid: str | int, restrict=False,
                                   comment: str = '', tags: Iterable[str] = ()):
        """Add bookmark"""
        pid = str(pid)
        method, url, data = px.illusts_bookmark_add(
            pid, restrict, comment, tags, host=self._host)
        return await self._request(method, url, data)

    async def user_illusts(self, uid: str | int, ids: Iterable[str | int] = (),):
        """Get user illusts by ids"""
        uid = str(uid)
        ids = tuple[str](str(i) for i in ids)
        method, url, params = px.user_illusts(uid, ids, host=self._host)
        return await self._request(method, url, params)

    async def user_illusts_bookmarks(self, uid: str | int, offset: int, limit=48,
                                     tag: str = None, rest: Literal["show", "hide"] = "show"):
        """Get user illusts bookmarks"""
        uid = str(uid)
        method, url, params = px.user_illusts_bookmarks(
            uid, offset, limit, tag, rest, host=self._host)
        return await self._request(method, url, params)

    async def user_works_latest(self, uid: str | int):
        """Get user latest works"""
        uid = str(uid)
        method, url, params = px.user_works_latest(uid, host=self._host)
        return await self._request(method, url, params)

    async def illust_recommend(self, pid: str | int | None = None,
                               illust_ids: Iterable[str | int] = (), limit: int = 18):
        """Get illust recommend"""
        if pid is not None:
            pid = str(pid)
        illust_ids = tuple[str](str(i) for i in illust_ids)
        method, url, params = px.illust_recommend(
            pid, illust_ids, limit, host=self._host)
        return await self._request(method, url, params)

    async def user(self, uid: str | int, full=1):
        """Get user info"""
        uid = str(uid)
        method, url, params = px.user(uid, full, host=self._host)
        return await self._request(method, url, params)

    async def tag_info(self, tag: str):
        """Get tag info"""
        method, url, params = px.tag_info(tag, host=self._host)
        return await self._request(method, url, params)

    @overload
    async def _request(self, method: str, url: str, payload,
                       is_ajax: Literal[True] = True) -> ObjDict: ...

    @overload
    async def _request(self, method: str, url: str, payload,
                       is_ajax: Literal[False]) -> httpx.Response: ...

    async def _request(self, method, url, payload, is_ajax=True):
        """Request Middle Layer
        Only returns the 'body' part of an ajax response
        """
        self._logger.debug(f"{method} {url}\n {_jdumps(payload)}")
        ex_headers = {"Accept": "application/json"} if is_ajax else {}
        for i in range(self._puller.max_retry):
            request = self.client.build_request(
                method, url, headers=ex_headers, **payload)
            self._logger.debug(f"Request: {request}")
            try:
                ret = await self.client.send(request, follow_redirects=True)

                self._logger.debug(f"{url} Response: {ret.text}")
                if ret.status_code == 200:
                    if not is_ajax:  # HTML
                        return ret
                    objd = ObjDict(ret.json())
                    if objd.error:
                        raise ValueError(f"{url} Error: "+objd.message)
                    return ObjDict(objd["body"])
                self._logger.warning(
                    f"Request {method} {url} failed: {ret.status_code}")
                ret.raise_for_status()
            except Exception as e:
                self._logger.error(f"Request {method} {url} failed:")
                self._logger.exception(e)
                await asyncio.sleep(min(1.5**i, 30))
                self._logger.warning(
                    f"{method} {url} {to_ordinal(i+1)} retrying...")
        # Retry failed
        raise RuntimeError(
            f"Request {method} {url} failed after {self._puller.max_retry} retries")
