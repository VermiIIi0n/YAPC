# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Callable, Sequence, Iterable, overload, Iterator, TypeVar, Any


__all__ = ["StrChain"]
ThisType = TypeVar("ThisType", bound="StrChain")


class StrChain(Sequence[str]):
    """
    ### StrChain: More than a convenient way to create strings.
    It is NOT a subclass of `str`, use `str()` to convert it to str.

    By default `callback` is `str`, so simply calling the instance will return the string.

    StrChain is immutable. Hash is the same as the string it represents.

    Usage:
    ```Python
    str_chain = StrChain()
    str_chain.hello.world() is "hello.world"
    # String can't start with '_' when using __getattr__ , use __getitem__ instead
    str_chain.["hello"]["_world"]() is "hello._world"

    path = StrChain(['/'], joint="/") # Initialize with a list and set custom joint
    path.home.user() is "/home/user"
    str(path + "home" + "user") == "/home/user" # Comparing with str
    (path.home.user + StrChain(["Downloads", "weird_shits"]))() == "/home/user/Downloads/weird_shits"

    # callback: used when calling StrChain, default is `str`
    # First argument is the StrChain itself followed by args and kwargs
    string = StrChain(callback=lambda x: '!'.join([i.lower() for i in x]))
    string.Hello.World() == "hello!world"
    ```
    And much more...
    """
    def __init__(
            self: ThisType,
            it: Iterable[str] | None = None,
            joint: str ='.',
            callback: Callable[..., Any] = str):
        """
        * `it`: Iterable[str], the initial string chain
        * `joint`: str, the joint between strings
        * `callback`: Callable[[StrChain, ...], Any], used when calling the StrChain instance
        """
        self._joint = joint
        self._callback = callback
        it = [it] if isinstance(it, str) else it
        self._list: list[str] = list(it or [])

    def __call__(self: ThisType, *args: Any, **kw: Any) -> Any:
        return self._callback(self, *args, **kw)

    def __create(self: ThisType, it: Iterable[str]) -> ThisType:
        return type(self)(it=it, joint=self._joint, callback=self._callback)

    def __len__(self: ThisType) -> int:
        return len(self._list)

    def __getattr__(self: ThisType, name: str) -> ThisType:
        if name.startswith('_'):
            raise AttributeError(f"{name} : String can't start with '_' when using __getattr__" +
                                  " , use __getitem__ instead")
        return self.__create(self._list + [name])

    @overload
    def __getitem__(self: ThisType, index: int) -> str:
        ...

    @overload
    def __getitem__(self: ThisType, s: slice) -> ThisType:
        ...

    @overload
    def __getitem__(self: ThisType, string: str) -> ThisType:
        ...

    def __getitem__(self: ThisType, value: int | slice | str) -> str | ThisType:
        if isinstance(value, int):
            return self._list[value]
        if isinstance(value, slice):
            return self.__create(self._list[value])
        if isinstance(value, str):
            return self.__create(self._list + [value])
        raise TypeError(f"Invalid type {type(value)}")

    def __eq__(self, other) -> bool:
        if type(other) is type(self):
            return self._list == other._list \
                   and self._joint == other._joint \
                   and self._callback == other._callback
        return False

    def __hash__(self: ThisType) -> int:
        return hash(str(self))

    def __add__(self: ThisType, other: Iterable[str] | str) -> ThisType:
        other = [other] if isinstance(other, str) else list(other)
        return self.__create(self._list + other)

    def __radd__(self: ThisType, other: Iterable[str] | str) -> ThisType:
        other = [other] if isinstance(other, str) else list(other)
        return self.__create(other + self._list)

    def __iadd__(self: ThisType, other: Iterable[str] | str) -> ThisType:
        return self + other

    def __mul__(self: ThisType, other: int) -> ThisType:
        return self.__create(self._list * other)

    def __rmul__(self: ThisType, other: int) -> ThisType:
        return self.__create(self._list * other)

    def __imul__(self: ThisType, other: int) -> ThisType:
        return self * other

    def __iter__(self: ThisType) -> Iterator[str]:
        return iter(self._list)

    def __str__(self: ThisType) -> str:
        return self._joint.join(self._list)

    def __repr__(self: ThisType) -> str:
        return self._joint.join(self._list)
