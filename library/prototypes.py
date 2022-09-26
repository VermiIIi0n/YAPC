"""Prorotypes for library elements."""
from __future__ import annotations
import hashlib
from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from bson.objectid import ObjectId
from bson.dbref import DBRef
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar, Type, Literal, overload, MutableMapping

__all__ = [
    "proper_setter", "UID", "DBRef", "Email", "OrderedItem", "FieldTypeError",
    "Source", "CreatorRef", "Creator", "Alias", "Tag", "Picture", "Geo",
    "FrameInfo", "Dimensions", "Pixiv", "Album", "Binary", "Shelf", "Library",
    "CreatorShelf", "TagShelf", "AlbumShelf",
]
UNSET = object()
UID = ObjectId
_V = TypeVar('_V')


class FieldTypeError(TypeError):
    ...


@overload
def proper_setter(value_type: Type[_V], default=UNSET,  # type: ignore
                  dissolve: bool = False, is_list: Literal[False] = False) -> Callable[..., _V]:
    ...


@overload
def proper_setter(value_type: Type[_V], default=UNSET,
                  dissolve: bool = False, is_list: Literal[True] = True) -> Callable[..., list[_V]]:
    ...


def proper_setter(value_type: Type[_V], default=UNSET,
                  dissolve: bool = False, is_list: bool = False) -> Callable[..., _V]:
    """### Set `property.getter` and `property.setter` in one line
    * `value_type` is the type of the value
    * `default` is the default value of the property
    * `dissolve` is whether to dissolve a dict into the `value_type` object 
    or a list of dicts into a list of `value_type` objects
    * `is_list` is whether the property is a list of `value_type` objects, 
    if `True`, will perform type checking and dissolving(if `dissolve`==`True`) 
    on each item in the list
    """
    # removes parametrization
    value_type = getattr(value_type, '__origin__', value_type)

    def deco(func: Callable) -> Callable:
        prop_name = func.__name__

        @property  # type: ignore
        def prop(self):
            try:
                return self[prop_name]
            except KeyError as e:
                if default is UNSET:
                    raise AttributeError(
                        f"Attribute {prop_name} not set.") from e
                return default

        @prop.setter  # type: ignore
        @wraps(func)
        def prop(self, value: _V | list[_V]):
            # Convert type
            if dissolve:
                if is_list:
                    if not isinstance(value, list):
                        raise FieldTypeError(f"Expected list for {prop_name}")
                    value = [v if isinstance(v, value_type)
                             else value_type(**v) for v in value]
                else:
                    value = value if isinstance(value, value_type) \
                        else value_type(**value)
            # Dynamic type checking
            if is_list:
                if not isinstance(value, list):
                    raise FieldTypeError(f"Expected list for {prop_name}")
                for v in value:
                    if not isinstance(v, value_type):
                        raise FieldTypeError(
                            f"Expected {value_type} for {prop_name}")
            else:
                if not isinstance(value, value_type):
                    raise FieldTypeError(
                        f"{prop_name} must be of type {value_type.__name__}")
            self[prop_name] = value
        return prop
    return deco  # type: ignore


class _Item(MutableMapping[str, Any]):
    """A `dict` wrapper, restricts its contents to a given set of keys."""

    def __init__(self, **kw):
        self._raw: dict[str, Any] = kw

    @property
    def raw(self) -> dict[str, Any]:
        """The raw `dict`."""
        return self._raw

    @raw.setter
    def raw(self, value: dict[str, Any]):
        self._raw = value

    def get(self, key: str, default: Any = UNSET) -> Any:
        """Get a value from the `dict`."""
        if default is UNSET:
            return self._raw[key]
        return self._raw.get(key, default)

    def pop(self, key: str, default: Any = UNSET) -> Any:
        """Pop a value from the `dict`."""
        if default is UNSET:
            return self._raw.pop(key)
        return self._raw.pop(key, default)

    def items(self):
        return self._raw.items()

    def __iter__(self):
        return iter(self._raw)

    def __contains__(self, key) -> bool:
        return key in self._raw

    def __getitem__(self, key: str) -> Any:
        return self._raw[key]

    def __setitem__(self, key: str, value: Any):
        self._raw[key] = value

    def __delitem__(self, key: str):
        del self._raw[key]

    def __len__(self) -> int:
        return len(self._raw)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.raw})"

    def __eq__(self, other) -> bool:
        if type(self) is type(other):
            return self.raw == other.raw
        return False

    __hash__ = None  # type: ignore[assignment]


class Source(_Item):
    """Represent a link to certain resource."""
    class types(Enum):
        """The type of source."""
        unavailable = "unavailable"
        filename = "filename"
        url = "url"
        bin = "bin"
        """Value is a referrer to a binary file in Binaries collection. 
        Not binary data itself."""
        picture = "picture"
        """Value is a referrer to a picture file in Pictures collection."""
        video = "video"
        """Value is a referrer to a video file in Videos collection."""
        music = "music"
        """Value is a referrer to a music file in Music collection."""
    _types_map = {"url": types.url, "filename": types.filename, "bin": types.bin,
                  "picture": types.picture, "video": types.video, "music": types.music,
                  "unavailable": types.unavailable}

    def __init__(self, type: types | str, value: str | UID | DBRef, label: str = None, **kw):
        super().__init__(**kw)
        self.type = type  # type: ignore
        self.value = value
        if label:
            self.label = label

    @property
    def type(self) -> types:
        return self._types_map[self["type"]]

    @type.setter
    def type(self, value: types | str):
        if isinstance(value, str):
            value = self._types_map[value]
        self["type"] = value.value

    @property
    def value(self) -> str | UID | DBRef:
        return self.get("value")

    @value.setter
    def value(self, value: str | UID | DBRef):
        self["value"] = value

    @proper_setter(str, '')
    def label(self, value: str):
        ...


class CreatorRef(_Item):
    """Represent a referrer to a Creator."""

    def __init__(self, name: str = "", id: UID = None,
                 role: str = None, label: str = None, **kw):
        super().__init__(**kw)
        self.name = name
        self.id = id
        if role:
            self.role = role
        if label:
            self.label = label

    @proper_setter(str)
    def name(self, value: str):
        ...

    @property
    def id(self) -> UID | None:
        return self.get('id', None)

    @id.setter
    def id(self, value: UID | None):
        self['id'] = value

    @proper_setter(str, '')
    def label(self, value: str):
        ...

    @proper_setter(str, '')
    def role(self, value: str):
        ...


class Alias(_Item):
    """Represent an alias for a Creator."""

    def __init__(self, name: str, label: str = ''):
        super().__init__()
        self.name = name
        self.label = label

    @proper_setter(str)
    def name(self, value: str):
        ...

    @proper_setter(str)
    def label(self, value: str):
        ...


class Email(_Item):
    """Represent an email."""

    def __init__(self, address: str, label: str = None):
        super().__init__()
        self.label = label or ''
        self.address = address

    @proper_setter(str)
    def address(self, value: str):
        ...

    @proper_setter(str)
    def label(self, value: str):
        ...


class OrderedItem(_Item):
    """Represent an item with an order."""

    def __init__(self, order: int):
        super().__init__()
        self.order = order

    @proper_setter(int)
    def order(self, value: int):
        ...


class FrameInfo(OrderedItem):
    """Represent a frame info."""

    def __init__(self, order: int, title: str, id: UID, duration: float = 0.0):
        """
        * `order`: the order of the frame.
        * `title`: the title of the frame.
        * `duration`: the duration of the frame in ms.
        * `id`: the id of the frame.
        """
        super().__init__(order)
        self.title = title
        self.duration = duration
        self.id = id

    @proper_setter(str)
    def title(self, value: str):
        ...

    @proper_setter(float)
    def duration(self, value: float):
        ...

    @proper_setter(UID)
    def id(self, value: UID):
        ...


class Dimensions(_Item):
    """Represent a Dimensions.
    * `width` and `height` are in pixels.
    * `vector` is whether the image is vector or not. If True, 
    `width` and `height` are ratios.
    """

    def __init__(self, width: int, height: int, vector: bool = False):
        super().__init__()
        self.width = width
        self.height = height
        self.vector = vector

    @proper_setter(int)
    def width(self, value: int):
        ...

    @proper_setter(int)
    def height(self, value: int):
        ...

    @proper_setter(bool)
    def vector(self, value: bool):
        ...


class Geo(_Item):
    """Represent a geo location."""
    class types(Enum):
        """The type of geo location."""
        point = "Point"
        """A point."""
    _types_map = {"Point": types.point}

    def __init__(self, type: types | str, coordinates: list[float]):
        super().__init__()
        self.type = type  # type: ignore
        self.coordinates = coordinates

    @property
    def type(self) -> types:
        return self._types_map[self["type"]]

    @type.setter
    def type(self, value: types | str):
        if isinstance(value, str):
            value = self._types_map[value]
        self["type"] = value.value

    @proper_setter(list[float])
    def coordinates(self, value: list[float]):
        """Longitude & Latitude."""
        ...


class Pixiv(_Item):
    """
    * `pid` Pixiv work id
    * `uid` Pixiv user id
    * `type` Pixiv type
    * `next` Next work pid
    * `prev` Previous work pid
    """
    class types(Enum):
        illust = 0
        manga = 1
        ugoira = 2
        novel = 3
    _types_map = (types.illust, types.manga, types.ugoira, types.novel)

    def __init__(self, pid: int = None, uid: int = None, type: types | int | None = None,
                 next: int = None, prev: int = None, original: bool = None,):
        super().__init__()
        if pid is not None:
            self.pid = pid
        if uid is not None:
            self.uid = uid
        if original is not None:
            self.original = original
        if type is not None:
            self.type = type  # type: ignore
        if next is not None:
            self.next = next
        if prev is not None:
            self.prev = prev

    @proper_setter(int)
    def pid(self, value: int):
        ...

    @proper_setter(int)
    def uid(self, value: int):
        ...

    @proper_setter(bool)
    def original(self, value: bool):
        ...

    @property
    def type(self) -> types:
        return self._types_map[self["type"]]

    @type.setter
    def type(self, value: types | int):
        if isinstance(value, int):
            value = self._types_map[value]
        self["type"] = value.value

    @proper_setter(int)
    def next(self, value: int):
        ...

    @proper_setter(int)
    def prev(self, value: int):
        ...


class _RichItem(_Item):
    """A Rich Item
    * `_id` The id of the item.
    * `saved_time` Time of being saved to the library
    * `last_modified`  Time of being modified
    * `ancestors` List of chains of collections 
    specifying which collection it belongs to
    * `tags` List of tag names
    """

    def __init__(
            self, _id: UID, saved_time: datetime = None, last_modified: datetime = None,
            ancestors: list[list[UID]] = None, tags: list[str] = None, archived: bool = False,
            **kw):
        super().__init__(**kw)
        self._id = _id
        self.archived = archived
        self.saved_time = saved_time or datetime.utcnow()
        self.last_modified = last_modified or datetime.utcnow()
        self.ancestors = ancestors or []
        self.tags = tags or []

    @proper_setter(UID)
    def _id(self, value: UID):
        ...

    @proper_setter(bool)
    def archived(self, value: bool):
        ...

    @proper_setter(datetime)
    def saved_time(self, value: datetime):
        ...

    @proper_setter(datetime)
    def last_modified(self, value: datetime):
        ...

    @proper_setter(list[UID], is_list=True)
    def ancestors(self, value: list[list[UID]]):
        ...

    @proper_setter(str, is_list=True)
    def tags(self, value: list[str]):
        ...


class Picture(_RichItem):
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
    class types(Enum):
        illust = 0
        manga = 1
        frame = 2
        cg = 3
        photo = 4
    _types_map = (types.illust, types.manga,
                  types.frame, types.cg, types.photo)

    def __init__(
        self, title: str, type: types | int, creator: CreatorRef, _id: UID,
        caption: str = '', sauce: str = '', rating: float = 3.0, albums: list[UID] = None,
        created_time: datetime = None, pixiv: Pixiv = None, archived: bool = False,
        frame_info: FrameInfo = None, src: list[Source] = None, dims: Dimensions = None,
        geo: Geo = None, saved_time: datetime = None, last_modified: datetime = None,
        ancestors: list[list[UID]] = None, tags: list[str] = None, **kw
    ):
        super().__init__(_id, saved_time, last_modified, ancestors, tags, archived, **kw)
        self.title = title
        self.type = type  # type: ignore
        self.creator = creator
        self.albums = albums or []
        self.caption = caption
        self.sauce = sauce
        self.rating = rating
        self.created_time = created_time or datetime(1970, 1, 1)
        self.src = src or []
        self.dims = dims or Dimensions(0, 0)
        if pixiv:
            self.pixiv = pixiv
        if frame_info:
            self.frame_info = frame_info
        if geo:
            self.geo = geo

    @proper_setter(str)
    def title(self, value: str):
        ...

    @property
    def type(self) -> types:
        return self._types_map[self["type"]]

    @type.setter
    def type(self, value: types | int):
        if isinstance(value, int):
            value = self._types_map[value]
        self["type"] = value.value

    @proper_setter(CreatorRef, dissolve=True)
    def creator(self, value: CreatorRef):
        ...

    @proper_setter(UID, is_list=True)
    def albums(self, value: list[UID]):
        ...

    @proper_setter(str)
    def caption(self, value: str):
        ...

    @proper_setter(str)
    def sauce(self, value: str):
        ...

    @proper_setter(float)
    def rating(self, value: float):
        ...

    @proper_setter(datetime)
    def created_time(self, value: datetime):
        ...

    @proper_setter(Pixiv, dissolve=True)
    def pixiv(self, value: Pixiv):
        ...

    @proper_setter(FrameInfo, dissolve=True)
    def frame_info(self, value: FrameInfo):
        ...

    @proper_setter(Source, dissolve=True, is_list=True)
    def src(self, value: list[Source]):
        ...

    @proper_setter(Dimensions, dissolve=True)
    def dims(self, value: Dimensions):
        ...

    @proper_setter(Geo, dissolve=True)
    def geo(self, value: Geo):
        ...


class Tag(_RichItem):
    """### Tag Class
    * `name` A unique name
    * `_id` UID
    * `aliases` List of aliases
    * `desc` Description
    * `members` List of DBRefs of members
    """

    def __init__(self, name: str, _id: UID, aliases: list[Alias] = None,
                 desc: str = '', members: list[DBRef] = None, archived: bool = False,
                 saved_time: datetime = None, last_modified: datetime = None,
                 ancestors: list[list[UID]] = None, cover: Source = None, **kw):
        super().__init__(_id, saved_time, last_modified, ancestors, None, archived, **kw)
        self.name = name
        self.cover = cover or Source(Source.types.unavailable, '')
        self.aliases = aliases or []
        self.desc = desc
        self.members = members or []
        del self["tags"]  # Tags are not allowed for tags

    @proper_setter(str)
    def name(self, value: str):
        ...

    @proper_setter(Source, dissolve=True)
    def cover(self, value: Source):
        ...

    @proper_setter(Alias, dissolve=True, is_list=True)
    def aliases(self, value: list[Alias]):
        ...

    @proper_setter(str)
    def desc(self, value: str):
        ...

    @proper_setter(DBRef, is_list=True)
    def members(self, value: list[DBRef]):
        ...


class Creator(_RichItem):
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
        self, name: str, _id: UID, avatar: Source = None, platform: str = '',
        user_id: str = '', homepage: str = '', primary: UID = None, gender: str = '',
        sub_identities: list[CreatorRef] = None, emails: list[str] = None,
        rating: float = 3.0, desc: str = '', birth: datetime = None, pixiv: Pixiv = None,
        death: datetime = None, works: list[DBRef] = None, archived: bool = False,
        saved_time: datetime = None, last_modified: datetime = None,
        ancestors: list[list[UID]] = None, tags: list[str] = None, **kw
    ):
        super().__init__(_id, saved_time, last_modified, ancestors, tags, archived, **kw)
        self.name = name
        self.avatar = avatar or Source(Source.types.unavailable, '')
        self.platform = platform
        self.user_id = user_id
        self.homepage = homepage
        if pixiv:
            self.pixiv = pixiv
        if primary:
            self.primary = primary
        if sub_identities:
            self.sub_identities = sub_identities
        self.emails = emails or []
        self.rating = rating
        self.gender = gender
        self.desc = desc
        self.birth = birth or datetime(1970, 1, 1, tzinfo=timezone.utc)
        self.death = death or datetime(1970, 1, 1, tzinfo=timezone.utc)
        self.works = works or []

    @proper_setter(str)
    def name(self, value: str):
        ...

    @proper_setter(Source, dissolve=True)
    def avatar(self, value: Source):
        ...

    @proper_setter(str)
    def platform(self, value: str):
        ...

    @proper_setter(str)
    def user_id(self, value: str):
        ...

    @proper_setter(str)
    def homepage(self, value: str):
        ...

    @proper_setter(Pixiv, dissolve=True)
    def pixiv(self, value: Pixiv):
        ...

    @proper_setter(UID)
    def primary(self, value: UID):
        ...

    @proper_setter(CreatorRef, dissolve=True, is_list=True)
    def sub_identities(self, value: list[CreatorRef]):
        ...

    @proper_setter(str, is_list=True)
    def emails(self, value: list[str]):
        ...

    @proper_setter(float)
    def rating(self, value: float):
        ...

    @proper_setter(str)
    def gender(self, value: str):
        ...

    @proper_setter(str)
    def desc(self, value: str):
        ...

    @proper_setter(datetime)
    def birth(self, value: datetime):
        ...

    @proper_setter(datetime)
    def death(self, value: datetime):
        ...

    @proper_setter(DBRef, is_list=True)
    def works(self, value: list[DBRef]):
        ...


class Album(_RichItem):
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
    class types(Enum):
        picture = 0
        music = 1
    _types_map = (types.picture, types.music)

    def __init__(
            self, title: str, type: types | int, creators: list[CreatorRef],
            _id: UID, cover: Source = None, desc: str = '', rating: float = 3.0,
            pixiv: Pixiv = None, members: list[UID] = None, created_time: datetime = None,
            saved_time: datetime = None, last_modified: datetime = None,
            ancestors: list[list[UID]] = None, tags: list[str] = None, archived: bool = False,
            **kw):
        super().__init__(_id, saved_time, last_modified, ancestors, tags, archived, **kw)
        self.title = title
        self.type = type  # type: ignore
        self.creators = creators
        self.cover = cover or Source(Source.types.unavailable, '')
        self.desc = desc
        self.rating = rating
        if pixiv:
            self.pixiv = pixiv
        self.members = members or []
        self.created_time = created_time or datetime.utcnow()

    @proper_setter(str)
    def title(self, value: str):
        ...

    @property
    def type(self) -> types:
        return self._types_map[self["type"]]

    @type.setter
    def type(self, value: types | int):
        if isinstance(value, int):
            value = self._types_map[value]
        self["type"] = value.value

    @proper_setter(CreatorRef, dissolve=True, is_list=True)
    def creators(self, value: list[CreatorRef]):
        ...

    @proper_setter(Source, dissolve=True)
    def cover(self, value: Source):
        ...

    @proper_setter(str)
    def desc(self, value: str):
        ...

    @proper_setter(float)
    def rating(self, value: float):
        ...

    @proper_setter(Pixiv, dissolve=True)
    def pixiv(self, value: Pixiv):
        ...

    @proper_setter(UID, is_list=True)
    def members(self, value: list[UID]):
        ...

    @proper_setter(datetime)
    def created_time(self, value: datetime):
        ...


class Binary(_RichItem):
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
    class types(Enum):
        general = 0
        image = 1
        video = 2
        exe = 3
        zip = 4
    _types_map = (types.general, types.image,
                  types.video, types.exe, types.zip)

    def __init__(
            self, name: str, type: types | int, value: bytes, _id: UID, desc: str = '',
            created_time: datetime = None, refs: list[DBRef] = None, md5: str = '',
            saved_time: datetime = None, last_modified: datetime = None,
            ancestors: list[list[UID]] = None, tags: list[str] = None, archived: bool = False,
            **kw):
        super().__init__(_id, saved_time, last_modified, ancestors, tags, archived, **kw)
        self.name = name
        self.type = type  # type: ignore
        self.desc = desc
        self.created_time = created_time or datetime.utcnow()
        self.value = value
        self.refs = refs or []
        self.md5 = md5 or hashlib.md5(value).hexdigest()

    @proper_setter(str)
    def name(self, value: str):
        ...

    @property
    def type(self) -> types:
        return self._types_map[self["type"]]

    @type.setter
    def type(self, value: types | int):
        if isinstance(value, int):
            value = self._types_map[value]
        self["type"] = value.value

    @proper_setter(str)
    def desc(self, value: str):
        ...

    @proper_setter(datetime)
    def created_time(self, value: datetime):
        ...

    @proper_setter(DBRef, is_list=True)
    def refs(self, value: list[DBRef]):
        ...

    @proper_setter(str)
    def md5(self, value: str):
        ...

    @property
    def value(self) -> bytes:
        return self["value"]

    @value.setter
    def value(self, value: bytes):
        self["value"] = value
        self.md5 = hashlib.md5(value).hexdigest()


class Collection(_RichItem):
    """### Collection Class
    * `name` Name
    * `_id` ID
    * `type` Collection type
    * `cover` Cover of the collection, a Source object
    * `desc` Description
    * `members` List of IDs of members
    * `created_time` Creation time
    """
    class types(Enum):
        general = 0
    _types_map = (types.general,)

    def __init__(
        self, name: str, _id: UID, type: types | int, cover: Source = None, desc: str = '',
        members: list[DBRef] = None, created_time: datetime = None,
        saved_time: datetime = None, last_modified: datetime = None,
        ancestors: list[list[UID]] = None, tags: list[str] = None,
        archived: bool = False, **kw
    ):
        super().__init__(_id, saved_time, last_modified, ancestors, tags, archived, **kw)
        self.name = name
        self.type = type  # type: ignore
        self.cover = cover or Source(Source.types.unavailable, '')
        self.desc = desc
        self.members = members or []
        self.created_time = created_time or datetime.utcnow()

    @proper_setter(str)
    def name(self, value: str):
        ...

    @property
    def type(self) -> types:
        return self._types_map[self["type"]]

    @type.setter
    def type(self, value: types | int):
        if isinstance(value, int):
            value = self._types_map[value]
        self["type"] = value.value

    @proper_setter(Source, dissolve=True)
    def cover(self, value: Source):
        ...

    @proper_setter(str)
    def desc(self, value: str):
        ...

    @proper_setter(DBRef, is_list=True)
    def members(self, value: list[DBRef]):
        ...

    @proper_setter(datetime)
    def created_time(self, value: datetime):
        ...


class Trash(_Item):
    def __init__(self, ref: DBRef, birth: datetime, death: datetime,
                 value: dict, _id: UID = None, **kw):
        super().__init__(**kw)
        self._id = _id or UID()
        self.ref = ref
        self.birth = birth
        self.death = death
        self.value = value

    @proper_setter(DBRef)
    def ref(self, value: DBRef):
        ...

    @proper_setter(datetime)
    def birth(self, value: datetime):
        ...

    @proper_setter(datetime)
    def death(self, value: datetime):
        ...

    @proper_setter(dict)
    def value(self, value: dict):
        ...


class Shelf(ABC):
    @abstractmethod
    async def get(self, _id):
        """Get by _id"""

    @abstractmethod
    async def contains(self, _id) -> bool:
        """Check if _id exists"""

    @abstractmethod
    async def upsert(self, doc):
        """upsert a document"""

    @abstractmethod
    async def delete(self, _id):
        """Move a document to trash"""

    @abstractmethod
    async def new_uid(self):
        """Generate a new UID"""

    @abstractmethod
    def __aiter__(self):
        """Iterate through all documents"""


class AlbumShelf(Shelf):
    @abstractmethod
    async def get_by_pid(self, pid) -> Any:
        """Get by Pixiv ID"""
    @abstractmethod
    async def pid_to_id(self, pid) -> UID | None:
        """Get _id by Pixiv ID"""


class CreatorShelf(Shelf):
    @abstractmethod
    async def get_by_uid(self, uid) -> Any:
        """Get by Pixiv user ID"""
    @abstractmethod
    async def uid_to_id(self, uid) -> UID | None:
        """Get _id by Pixiv user ID"""


class TagShelf(Shelf):
    @abstractmethod
    async def get_by_name(self, tname) -> Any:
        """Get by tag name"""
    @abstractmethod
    async def name_to_id(self, tname) -> UID | None:
        """Get _id by tag name"""


class Library(ABC):
    @abstractmethod
    def get_shelf(self, name) -> Shelf:
        ...

    @abstractmethod
    async def close(self):
        ...

    @abstractmethod
    def __getattr__(self, name) -> Shelf:
        ...

    @property
    @abstractmethod
    def Pictures(self) -> Shelf:
        ...

    @property
    @abstractmethod
    def Creators(self) -> CreatorShelf:
        ...

    @property
    @abstractmethod
    def Albums(self) -> AlbumShelf:
        ...

    @property
    @abstractmethod
    def Tags(self) -> TagShelf:
        ...

    @property
    @abstractmethod
    def Binaries(self) -> Shelf:
        ...

    @property
    @abstractmethod
    def Collections(self) -> Shelf:
        ...

    @property
    @abstractmethod
    def Trashbin(self):
        ...
