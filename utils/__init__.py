# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import sys
import ujson as json
import asyncio
import inspect
import nest_asyncio
from http.cookiejar import CookieJar, Cookie
from functools import wraps, partial
from contextvars import copy_context
from typing import Awaitable, Callable, Any, Generator, AsyncGenerator, Iterable
from typing import TYPE_CHECKING, TypeVar, Type
from . import sidelogging
from .sidelogging import *
from . import EventHooks
from .EventHooks import *
from .StrChain import StrChain
from .ObjDict import ObjDict

__all__ = [
    "str_to_class",
    "real_dir",
    "real_path",
    "version_cmp",
    "wipe_line",
    "validate_json",
    "to_ordinal",
    "with_typehint",
    "sync_await",
    "ensure_async",
    "to_async",
    "to_async_iter",
    "DummyAioFileStream",
    ] \
    + ["StrChain"] \
    + ["ObjDict"] \
    + EventHooks.__all__ \
    + sidelogging.__all__

T = TypeVar('T')

def str_to_class(class_name: str, module: str = "__main__") -> type:
    return getattr(sys.modules[module], class_name)


def real_dir(file: str = None) -> str:
    try:
        file = getattr(sys.modules["__main__"], "__file__") if file is None else file
    except AttributeError:
        file = ''
    return os.path.dirname(os.path.realpath(file))


def real_path(path: str):
    if not path:
        return path
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    path = os.path.normpath(path)
    if path == os.path.abspath(path):
        return os.path.realpath(path)
    return os.path.join(real_dir(), path)

def version_cmp(v1:str, v2:str):
    v1s = v1.split('.')
    v2s = v2.split('.')
    for i in range(min(len(v1s), len(v2s))):
        dt = int(v1s[i]) - int(v2s[i])
        if dt:
            return dt
    return len(v1s) - len(v2s)

def wipe_line():
    print('\r' + ' ' * (os.get_terminal_size().columns), end = '\r')

def validate_json(data: str) -> bool:
    try:
        json.loads(data)
        return True
    except Exception as e:
        return False

def to_ordinal(num: int) -> str:
    if num % 100 in [11, 12, 13]:
        return f"{num}th"
    else:
        return f"{num}{['th', 'st', 'nd', 'rd'][num % 10 if num % 10 < 4 else 0]}"

def sync_await(coro: Awaitable[T], loop: asyncio.AbstractEventLoop=None) -> T:
    loop = loop or asyncio.get_event_loop()
    nest_asyncio.apply(loop)
    return loop.run_until_complete(coro)

def merge_ancestors(ancestors: Iterable[list]):
    familytree = list(ancestors)
    if len(familytree) <= 1:
        return familytree or [[]]
    familytree.sort(key = lambda x: len(x))
    for i in range(len(familytree)):
        for j in range(i + 1, len(familytree)):
            if set(familytree[i]).issubset(set(familytree[j])):
                familytree.remove(familytree[i])
                break
    return familytree


def gen_table(rows: Iterable[str|None], max_length: int=0) -> str:
    """Generate MySQL like table digest"""
    rows = list(rows)
    max_length = max_length or int(min(70, 3*len(rows)/0.618))
    outs = ['+'+'-'*(max_length+2)+'+']
    for row in rows:
        if row is None:
            outs.append('|'+'-'*(max_length+2)+'|')
        else:
            outs.append('| ' + row[:max_length].ljust(max_length) + (
                    ' |' if len(row) <= max_length else '->'))
    outs.append(outs[0])
    return '\n'+'\n'.join(outs)+'\n'

def selenium_cookies_to_jar(raws: list[dict[str, str]]) -> CookieJar:
    """Converts selenium cookies to http.cookiejar.CookieJar"""
    jar = CookieJar()
    for r in raws:
        cookie = Cookie(**{  # type: ignore
            "version": 0,
            "name": r["name"],
            "value": r["value"],
            "port": None,
            "port_specified": False,
            "domain": r["domain"],
            "domain_specified": bool(r["domain"]),
            "domain_initial_dot": r["domain"].startswith("."),
            "path": r["path"],
            "path_specified": bool(r["path"]),
            "secure": r["secure"],
            "expires": r["expiry"],
            "discard": True,
            "comment": None,
            "comment_url": None,
            "rest": {"HttpOnly": None},
            "rfc2109": False,
        })
        jar.set_cookie(cookie)
    return jar

class DummyAioFileStream:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def write(self, data):
        pass

    async def flush(self):
        pass

    async def close(self):
        pass

############# codes from other places ##############

#### TinyDB ####

def with_typehint(baseclass: Type[T]):
    """
    Add type hints from a specified class to a base class:

    >>> class Foo(with_typehint(Bar)):
    ...     pass

    This would add type hints from class ``Bar`` to class ``Foo``.

    Note that while PyCharm and Pyright (for VS Code) understand this pattern,
    MyPy does not. For that reason TinyDB has a MyPy plugin in
    ``mypy_plugin.py`` that adds support for this pattern.
    """
    if TYPE_CHECKING:
        # In the case of type checking: pretend that the target class inherits
        # from the specified base class
        return baseclass

    # Otherwise: just inherit from `object` like a regular Python class
    return object

#### aiocqhttp ####

def ensure_async(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    if asyncio.iscoroutinefunction(func):
        return func
    else:
        return to_async(func)

#### quart.utils ####

def to_async(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    """Ensure that the sync function is run within the event loop.
    If the *func* is not a coroutine it will be wrapped such that
    it runs in the default executor (use loop.set_default_executor
    to change). This ensures that synchronous functions do not
    block the event loop.
    """

    @wraps(func)
    async def _wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, copy_context().run, partial(func, *args, **kwargs)
        )
        if inspect.isgenerator(result):
            return to_async_iter(result)
        else:
            return result

    return _wrapper


def to_async_iter(iterable: Generator[Any, None, None]) -> AsyncGenerator[Any, None]:
    async def _gen_wrapper() -> AsyncGenerator[Any, None]:
        # Wrap the generator such that each iteration runs
        # in the executor. Then rationalise the raised
        # errors so that it ends.
        def _inner() -> Any:
            # https://bugs.python.org/issue26221
            # StopIteration errors are swallowed by the
            # run_in_exector method
            try:
                return next(iterable)
            except StopIteration as e:
                raise StopAsyncIteration() from e

        loop = asyncio.get_running_loop()
        while True:
            try:
                yield await loop.run_in_executor(None, copy_context().run, _inner)
            except StopAsyncIteration:
                return

    return _gen_wrapper()
