"""Pullers Collection"""
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import asyncio
from asyncio import Future
from typing import Iterable, Mapping, Any, Callable, Awaitable, Sequence, TypeVar, TYPE_CHECKING
from abc import abstractmethod
from httpx import Request, Response, Timeout
from utils import DummyAioFileStream as Dummyf, EventHint as Hint, LoggerLike, to_ordinal
from utils import ActionChain, AsyncActionChain, EventHook, StrChain
from utils import ensure_async
from httpx._types import HeaderTypes, ProxiesTypes, CookieTypes, QueryParamTypes
import aiofiles as aiof
import httpx

if TYPE_CHECKING:
    import rich.progress

__all__ = [
    "Request",
    "Response",
    "HeaderTypes",
    "ProxiesTypes",
    "CookieTypes",
    "QueryParamTypes",
    "HttpActionType",
    "AsyncPuller",
    "AsyncPullerEventHook",
    "AsyncActionChain",
    "AsyncHttpActionChain",
    "MaxRetryReached",
    "FileCorrupted",
    "Modifier",
]


class MaxRetryReached(Exception):
    """Raised when the maximum number of retries is reached."""


class BasePuller:
    """Base class for pullers."""
    @property
    def event_hooks(self) -> EventHook:
        """Event hook for this puller."""
        raise NotImplementedError()
    
    @abstractmethod
    def pull(self, url: str, path: str) -> Any:
        """Pull the file from the url to the path."""


class BaseWorker:
    """Base class for workers."""


class BaseMaster:
    """Base class for masters."""


HttpActionType = Callable[[Request | Response], Awaitable]
ActionVar = TypeVar('ActionVar', bound=Callable)


class AsyncHttpActionChain(ActionChain[HttpActionType]):
    """Async Http Action Chain"""

    def __init__(self, actions: Iterable[HttpActionType] = None) -> None:
        super().__init__(actions=actions)


class AsyncPullerEventHook(EventHook):
    """Async Puller Event Hook"""

    def __init__(self, chain: Mapping[str, Iterable[Callable[..., Any]]] | None = None):
        self.hook("request", AsyncHttpActionChain())
        self.hook("response", AsyncHttpActionChain())
        self.hook("worker.spawn", AsyncActionChain())
        self.hook("worker.destroy", AsyncActionChain())
        self.hook("worker.start", AsyncActionChain())
        self.hook("worker.response_get", AsyncActionChain())
        self.hook("worker.bytes_get", AsyncActionChain())
        self.hook("worker.retry", AsyncActionChain())
        self.hook("worker.success", AsyncActionChain())
        self.hook("worker.fail", AsyncActionChain())
        self.hook("puller.spawn", AsyncActionChain())
        self.hook("puller.destroy", AsyncActionChain())
        self.hook("puller.join", AsyncActionChain())
        EventHook.__init__(self, chain=chain)


class AsyncWorker(BaseWorker):
    def __init__(
        self,
        puller: AsyncPuller,
        url: str,
        path: str | None,
        retry: int,
        overwrite: bool,
        *,
        future: Future | None = None,
        timeout: Timeout | float | None,
        extra_headers: HeaderTypes | None,
        extra_params: QueryParamTypes | None,
        extra_cookies: CookieTypes | None,
        **kw
    ):
        self.puller = puller
        self.url = url
        self.path = path
        self.future = future
        self.timeout = timeout
        self.max_retry = retry
        self.overwrite = overwrite
        self.extra_headers = extra_headers
        self.extra_params = extra_params
        self.extra_cookies = extra_cookies
        self.kw = kw
        self.event_hooks = AsyncPullerEventHook(
            self.puller.event_hooks)  # snapshot

    async def run(self):
        """Run the worker."""
        event_hooks = self.event_hooks
        try:
            await event_hooks.aemit("worker.start", self)
            if self.path and os.path.exists(self.path) and not self.overwrite:
                raise FileExistsError(f"{self.path} already exists")
            client = self.puller.client
            retry = 0
            while True:
                try:
                    # Open file in async mode, if path is None, write to void
                    async with aiof.open(self.path, "wb") if self.path else Dummyf() as f:
                        # Establish connection
                        async with client.stream(
                            method=self.kw.pop("method", "GET"),
                            url=self.url,
                            params=self.extra_params,
                            headers=self.extra_headers,
                            cookies=self.extra_cookies,
                            timeout=self.timeout or self.puller.client.timeout,
                            **self.kw
                        ) as r:
                            await event_hooks.aemit("worker.response_get", self, r)
                            # Iterate over response chunks
                            async for chunk in r.aiter_bytes(chunk_size=2**18):  # 256KB
                                await event_hooks.aemit("worker.bytes_get", self, r, chunk)
                                await f.write(chunk)
                            await f.flush()
                            await event_hooks.aemit("worker.success", self, r)
                    self.future.set_result(self.path)  # set result for placeholder
                    break  # Quit successfully
                # Retry on network IO error
                except (httpx.HTTPError, httpx.StreamError) as e:
                    retry += 1
                    if retry > self.max_retry:
                        raise MaxRetryReached(f"Max retry reached: {retry} times") from e
                    await event_hooks.aemit("worker.retry", self, e, retry)
                    await asyncio.sleep(min(30, 1.7 ** retry))
        # Fatal Errors
        except (Exception, asyncio.CancelledError) as e:
            handled = await event_hooks.aemit("worker.fail", self, e)
            if True not in handled:
                self.future.cancel()
                raise e
        finally:
            await event_hooks.aemit("worker.destroy", self)
            self.puller._workers.get_nowait()
            self.puller._workers.task_done()  # workers count - 1

    def __repr__(self) -> str:
        return f"AsynWorker({self.url}, {self.path})"


class AsyncMaster(BaseMaster):
    def __init__(self, puller: AsyncPuller):
        self.puller = puller

    async def run(self):
        """Run the master."""
        try:
            buffer = self.puller._buffer
            workers = self.puller._workers
            while True:
                worker = await buffer.get()
                if worker is None:  # Kill signal
                    buffer.task_done()
                    break
                await workers.put(worker)  # blocks when max_workers reached
                self.puller._loop.create_task(worker.run())
                buffer.task_done()
                await asyncio.sleep(self.puller.interval)  # sleep a while
        finally:
            self.puller._master = None  # Reset master


class AsyncPuller(BasePuller):
    """### Async Puller"""
    def __init__(
        self,
        *,
        headers: HeaderTypes | None = None,
        params: QueryParamTypes | None = None,
        proxies: ProxiesTypes | None = None,
        cookies: CookieTypes | None = None,
        event_hooks: Mapping[str, Sequence[Callable]] = None,
        interval: float = 0.0,
        max_workers: int = 8,
        timeout: Timeout | float | None = 10,
        retry: int = 3,
        overwrite: bool = False,
        loop: asyncio.AbstractEventLoop | None = None,
        **kw
    ):
        """### Init Puller
        * `headers`: Default headers for all requests
        * `params`: Default query params for all requests
        * `proxies`: Default proxies for all requests
        * `cookies`: Default cookies for all requests
        * `event_hooks`: dict[str, Iterable[Callable]]
        * `interval`: Interval between each request
        * `max_workers`: Max downloading threads count
        * `timeout`: Timeout for each request
        * `retry`: Max retry times for each request
        * `overwrite`: Overwrite existing files
        * `loop`: Event loop
        * `**kw`: Other keyword arguments for httpx.Client
        """
        self._loop = loop
        self.interval = interval
        self.max_retry = max(retry, 0)
        self.overwrite = overwrite

        self._proxies = proxies
        self._master: AsyncMaster | None = None
        self._buffer: asyncio.Queue = asyncio.Queue()  # Pending workers
        self._workers: asyncio.Queue = asyncio.Queue(
            maxsize=max_workers)  # Running workers

        limits = httpx.Limits(
            max_connections=None,
            max_keepalive_connections=None,
            keepalive_expiry=10)

        self._client = httpx.AsyncClient(
            headers=headers,
            params=params,
            proxies=proxies,
            cookies=cookies,
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            http2=True,
            **kw
        )
        self.event_hooks = event_hooks or AsyncPullerEventHook()

        # Set up event hook
        def subscribe(event: StrChain, action: ActionVar) -> ActionVar:
            ev = str(event)
            self._event_hooks[ev].append(action)
            if ev in ["request", "response"]:
                self._client.event_hooks = self._event_hooks  # type: ignore[assignment]
            return action

        self._on = PullerEventHint(strchain=StrChain(joint='.', callback=subscribe))

    @property
    def client(self):
        return self._client

    @property
    def loop(self):
        return self._loop

    @property
    def headers(self):
        """Get headers."""
        return self._client.headers

    @headers.setter
    def headers(self, value: HeaderTypes):
        """Set headers for all requests."""
        self._client.headers = value  # type: ignore[assignment]

    @property
    def cookies(self):
        return self._client.cookies

    @cookies.setter
    def cookies(self, value: CookieTypes):
        """Set cookies for all requests."""
        self._client.cookies = value  # type: ignore[assignment]

    @property
    def params(self):
        return self._client.params

    @params.setter
    def params(self, value: QueryParamTypes):
        """Set params for all requests."""
        self._client.params = value  # type: ignore[assignment]

    @property
    def event_hooks(self):
        return self._event_hooks

    @event_hooks.setter
    def event_hooks(self, hooks: Mapping[str, Sequence[Callable]]):
        """Set event hooks for all requests."""
        self._event_hooks = AsyncPullerEventHook(hooks)  # deepcopy
        self._client.event_hooks = self._event_hooks  # type: ignore[assignment]

    @property
    def on(self):
        """Shortcut for `Puller.event_hooks.on`"""
        return self._on

    @property
    def proxies(self):
        return self._proxies

    async def pull(
        self,
        url: str,
        path: str | None,
        *,
        extra_headers: HeaderTypes | None = None,
        extra_params: QueryParamTypes | None = None,
        extra_cookies: CookieTypes | None = None,
        timeout: Timeout | float | None = 0,
        retry: int | None = None,
        overwrite: bool | None = None,
        **kw
    ) -> Future:
        """
        ### Asyncronously pull a file from a url.
        File will be decompressed and saved in binary mode.

        Returns a `Future` instance refer to the path of the downloaded file.
        * `url`: url to pull from
        * `path`: path to save to, set to `None` or `""` will not save file

        Optional Parameters:
        * `extra_headers`: extra headers to add to request
        * `extra_params`: extra params to add to request
        * `extra_cookies`: extra cookies to add to request
        * `timeout`: timeout for this request, set to None will be no limit, 0 for default
        * `retry`: retry times for this request, set to None will use default
        * `overwrite`: overwrite file if exists, set to None will use default
        * `**kw`: extra keyword arguments for httpx.stream
        """
        timeout = self.client.timeout if timeout == 0 else timeout
        self._loop = self.loop or asyncio.get_running_loop()
        if self._master is None:
            self._master = AsyncMaster(self)
            self._loop.create_task(self._master.run())
        future: Future = Future()  # A placeholder for the worker.run() task
        worker = AsyncWorker(
            self,
            url=url,
            path=path,
            extra_headers=extra_headers,
            extra_params=extra_params,
            extra_cookies=extra_cookies,
            future=future,
            timeout=timeout,
            retry=retry or self.max_retry,
            overwrite=overwrite or self.overwrite,
            **kw
        )
        await self._event_hooks.aemit("worker.spawn", worker)
        await self._buffer.put(worker)
        return future

    async def join(self) -> None:
        """### Wait for all workers to finish."""
        await self._event_hooks.aemit("puller.join", self)
        await self._buffer.join()  # Make sure no pending tasks
        await self._workers.join()  # Make sure all tasks are done

    async def aclose(self):
        await self.join()  # Make sure all tasks are done
        await self._buffer.put(None)  # Kill master
        await self._event_hooks.aemit("puller.destroy", self)
        await self._client.aclose()

    async def __aenter__(self) -> AsyncPuller:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.aclose()
        return False
    
    def __repr__(self):
        return f"{self.__class__.__name__}:\n"+\
            f"  max_retry: {self.max_retry}\n"+\
            f"  overwrite: {self.overwrite}\n"+\
            f"  headers: {self.headers}\n"+\
            f"  params: {self.params}\n"+\
            f"  cookies: {self.cookies}\n"+\
            f"  proxies: {self.proxies}\n"+\
            f"  event_hooks: {self.event_hooks}\n"
        

################### Useful Modifiers #####################


class Modifier:
    progress = None

    @classmethod
    def show_progress(
        cls,
        puller: BasePuller,
        desc_len: int = os.get_terminal_size().columns//3,
        delay_on_finish: float | None = 0.5,
        progress: rich.progress.Progress | None = None,
    ) -> None:
        """
        ### Show progress of all tasks.
        * `puller`: Puller instance
        * `desc_len`: max length of url description
        * `delay_on_finish`: time to remove finished progress bar, set to `None` to keep it
        * `progress`: rich.progress.Progress instance, set to `None` to use default one
        """
        from rich.progress import Progress
        if cls.progress is None:
            cls.progress = Progress(refresh_per_second=30)
        _progress = progress or cls.progress

        if isinstance(puller, AsyncPuller):
            @puller.on.worker.start
            async def create_task(event: str, worker: AsyncWorker):
                nonlocal puller
                progress = _progress  # In case outer progress is changed
                desc = worker.url.split("://")[-1]
                if len(desc) > desc_len:
                    desc = desc[:(desc_len-3)//2] + "..." + \
                        desc[-(desc_len-3)//2:]
                progress.start()  # start progress bar
                task = progress.add_task(desc)
                total = 0
                failed = False

                @worker.event_hooks.on.worker.response_get
                async def get_total(event: str, worker: AsyncWorker, r: Response):
                    nonlocal task
                    nonlocal total
                    total = int(r.headers.get("Content-Length", 0))
                    # type: ignore[arg-type]
                    progress.update(task, total=total or 100)

                @worker.event_hooks.on.worker.bytes_get
                async def update_task(ev: str, w: AsyncWorker, r: Response, b: bytes):
                    nonlocal task
                    nonlocal total
                    if total:
                        # type: ignore[arg-type]
                        progress.update(task, completed=r.num_bytes_downloaded)

                @worker.event_hooks.on.worker.fail
                async def fail_task(ev: str, w: AsyncWorker, e: Exception):
                    nonlocal failed
                    nonlocal task
                    failed = True
                    if isinstance(e, FileExistsError):
                        progress.remove_task(task)

                @worker.event_hooks.on.worker.destroy
                async def remove_task(event: str, worker: AsyncWorker):
                    nonlocal task
                    nonlocal total
                    if not failed:
                        if not total:  # Show cpmpleted for unknown size
                            progress.update(task, total=1, completed=1)
                        progress.refresh()
                        if delay_on_finish is not None:
                            await asyncio.sleep(delay_on_finish)
                            progress.update(task, visible=False, refresh=True)
                            progress.remove_task(task)
                    if progress.finished:
                        progress.stop()

    @staticmethod
    def ignore_failure(puller: BasePuller) -> None:
        """
        ### Ignore all exceptions.
        * `puller`: Puller instance
        """
        if isinstance(puller, AsyncPuller):
            @puller.on.worker.fail
            async def ignore_failure(event: str, worker: AsyncWorker, e: Exception):
                return True

    @staticmethod
    def ignore_file_exists(puller: BasePuller) -> None:
        """
        ### Ignore `FileExistsError`.
        * `puller`: Puller instance
        """
        if isinstance(puller, AsyncPuller):
            @puller.on.worker.fail
            async def ignore_file_exists(event: str, worker: AsyncWorker, e: Exception):
                if isinstance(e, FileExistsError):
                    return True

    @staticmethod
    def raise_for_status(puller: BasePuller) -> None:
        """
        ### Raise exception on non-200 status.
        * `puller`: Puller instance
        """
        if isinstance(puller, AsyncPuller):
            @puller.on.worker.response_get
            async def raise_for_status(event: str, worker: AsyncWorker, r: Response):
                r.raise_for_status()

    @staticmethod
    def add_logging(puller: BasePuller, logger: LoggerLike) -> None:
        """
        ### Add logging for events.
        * `puller`: Puller instance
        * `logger`: logger-like instance
        """
        if isinstance(puller, AsyncPuller):
            @puller.on.puller.spawn
            async def p_log_spawn(event: str, puller: AsyncPuller):
                logger.debug(f"Puller spawned. {puller}")

            @puller.on.puller.join
            async def p_log_join(event: str, puller: AsyncPuller):
                logger.debug(f"Puller joined. {puller}")

            @puller.on.puller.destroy
            async def p_log_destroy(event: str, puller: AsyncPuller):
                logger.debug(f"Puller destroyed. {puller}")

            @puller.on.worker.spawn
            async def log_spawn(event: str, worker: AsyncWorker):
                logger.debug(f"Spawned worker {worker}")

            @puller.on.worker.start
            async def log_start(event: str, worker: AsyncWorker):
                logger.debug(f"Start: {worker}")

            @puller.on.worker.response_get
            async def log_response(event: str, worker: AsyncWorker, r: Response):
                logger.debug(f"Response: {r.status_code}  {r.url}")

            @puller.on.worker.bytes_get
            async def log_bytes(event: str, worker: AsyncWorker, r: Response, b: bytes):
                logger.debug(f"Bytes size: {len(b)} from {r.url}")

            @puller.on.worker.retry
            async def log_retry(event: str, worker: AsyncWorker, e: Exception, retry: int):
                logger.debug(f"Retry: {worker} at {to_ordinal(retry)} time")

            @puller.on.worker.destroy
            async def log_destroy(event: str, worker: AsyncWorker):
                logger.debug(f"Destroy: {worker}")

            @puller.on.worker.fail
            async def log_fail(event: str, worker: AsyncWorker, e: Exception):
                logger.error(f"Fail: {worker} due to {e}")
                logger.exception(e)

    @staticmethod
    def on_every_event(puller: BasePuller, func: Callable) -> None:
        """
        ### Call function on every event.
        * `puller`: Puller instance
        * `func`: function to call
        """
        if isinstance(puller, AsyncPuller):
            @puller.on.puller.spawn
            @puller.on.puller.join
            @puller.on.puller.destroy
            @puller.on.worker.spawn
            @puller.on.worker.start
            @puller.on.worker.response_get
            @puller.on.worker.bytes_get
            @puller.on.worker.retry
            @puller.on.worker.destroy
            @puller.on.worker.fail
            async def on_every_event(*args, **kw):
                await ensure_async(func)(*args, **kw)

    @staticmethod
    def clear_hooks(puller: BasePuller) -> None:
        """
        ### Clear all hooks.
        * `puller`: Puller instance
        """
        puller.event_hooks.clear()


#### Start Hinting: Add hints for event names ####

class on_puller_hint(Hint):
    @property
    def spawn(self):
        """Callback Type: (event_name: str, AsyncPuller) -> None"""
        return self._chain.spawn
    @property
    def destroy(self):
        """Callback Type: (event_name: str, AsyncPuller) -> None"""
        return self._chain.destroy
    @property
    def join(self):
        """Callback Type: (event_name: str, AsyncPuller) -> None"""
        return self._chain.join


class on_worker_hint(Hint):
    @property
    def spawn(self):
        """Callback Type: (event_name: str, AsyncWorker) -> None"""
    @property
    def destroy(self):
        """Callback Type: (event_name: str, AsyncWorker) -> None"""
    @property
    def start(self):
        """Callback Type: (event_name: str, AsyncWorker) -> None"""
    @property
    def response_get(self):
        """Callback Type: (event_name: str, AsyncWorker, Response) -> None"""
    @property
    def bytes_get(self):
        """Callback Type: (event_name: str, AsyncWorker, Response, bytes) -> None"""
    @property
    def retry(self):
        """Callback Type: (event_name: str, AsyncWorker, Exception, retry: int) -> None"""
    @property
    def success(self):
        """Callback Type: (event_name: str, AsyncWorker) -> None"""
    @property
    def fail(self):
        """Callback Type: (event_name: str, AsyncWorker, Exception) -> bool:
        whether to ignore the exception"""

class PullerEventHint(Hint):
    """Puller Event Hint."""
    @property
    def puller(self) -> on_puller_hint:
        return self._chain.puller # type: ignore
    @property
    def worker(self) -> on_worker_hint:
        return self._chain.worker # type: ignore
    @property
    def request(self):
        """Callback Type: (Request) -> None"""
        return self._chain.request
    @property
    def response(self):
        """Callback Type: (Response) -> None"""
        return self._chain.response

### End Hinting ###
