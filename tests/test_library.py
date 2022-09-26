import pytest
import tempfile
import os
import ujson as json
from uuid import uuid4
from asynctinydb import JSONStorage
from typing import AnyStr
from library._extended_json import json_convert, r_recover
from library import prototypes as proto
from library import tinyend
from bson.dbref import DBRef
from bson.objectid import ObjectId
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_xstorage():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = JSONStorage(os.path.join(tmpdir, "test.json"))
        @storage.on.write.pre
        async def _convert(ev: str, s, data: dict) -> None:
            new = json_convert(data)
            data.update(new)
        @storage.on.write.post
        async def validate(ev: str, s, data: AnyStr) -> None:
            try:
                json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError("File Corrupted, abort writing") from e
        @storage.on.read.post
        async def _recover(ev: str, s, data: dict) -> None:
            new = r_recover(data)
            data.update(new)
        data = {
            "int": 12345,
            "float": 12345.6789,
            "str": "Hello, World!",
            "list": [1, 2, 3, 4, 5],
            "dict": {"a": 1, "b": 2, "c": 3},
            "binary": b"Hello, World!",
            "dbref": DBRef("test", ObjectId("5f9f1b9b4b9b9b9b9b9b9b9b")),
            "datetime": datetime.utcnow().astimezone(timezone.utc),
            "objectid": ObjectId("5f9f1b9b4b9b9b9b9b9b9b9b"),
            "uuid": uuid4(),
            "recursive": {
                "ref": [DBRef("test", ObjectId("5f9f1b9b4b9b9b9b9b9b9b9b")), ObjectId("5f9f1b9b4b9b9b9b9b9b9b9b"), uuid4()]
            }
        }
        await storage.write(data)
        assert await storage.read() == data

def test_proto_item():
    item = proto._Item()
    data = {
        "int": 12345,
        "float": 12345.6789,
        "str": "Hello, World!",
    }
    item.raw = data
    for k,v in item.items():
        assert data[k] == v
    assert len(item) == len(data)
    assert item.raw == data
    assert item.raw == dict(item)
    assert item.get("NotExist", "Default") == "Default"
    assert item.get("int") == 12345
    assert item.pop("int") == 12345
    assert item.pop("int", "Default") == "Default"
    with pytest.raises(KeyError):
        item.pop("int")
    with pytest.raises(KeyError):
        item.get("int")
    item["int"] = 12345
    assert item["int"] == 12345
    assert "int" in item
    del item["int"]
    assert [i for i in item] == ["float", "str"]

def test_proto_source():
    Source = proto.Source
    s = Source(Source.types.filename, "test.json")
    assert s.type == Source.types.filename
    assert s.value == "test.json"
    assert s.label == ''
    s.type = Source.types.url
    s.value = "http://localhost:8080"
    s.label = "Test"
    assert s.type == Source.types.url
    assert s.value == "http://localhost:8080"
    assert s.label == "Test"
    s2 = Source(**s.raw)
    assert s2.type == Source.types.url
    assert s2.value == "http://localhost:8080"
    assert s2.label == "Test"
    assert s == s2
    assert s2.raw == r_recover(json_convert(s2.raw))

def test_proto_creatorref():
    Ref = proto.CreatorRef
    r = Ref("author")
    assert r.name == "author"
    assert r.id is None
    r = Ref("author2", proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b"))
    assert r.id == proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b")

def test_proto_picture():
    Pic = proto.Picture
    p = Pic("test.png", Pic.types.illust, proto.CreatorRef("author"),proto.UID(), geo=proto.Geo("Point",[2,4]),
    frame_info=proto.FrameInfo(1,"test_frame", id=proto.UID(), duration=50.0), pixiv=proto.Pixiv(12345, 6676))
    data = json_convert(p)
    p2 = Pic(**r_recover(data))
    assert p.raw == p2.raw
    assert p == p2
    assert p2.raw != r_recover(json_convert(p2.raw)) # raw is not that "raw-ish"

def test_proto_tag():
    Tag = proto.Tag
    Alias = proto.Alias
    DBRef = proto.DBRef
    t = Tag("test", proto.UID(),
    aliases=[Alias("test2"), Alias("test3")],
    members= [DBRef("test", proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b")), DBRef("test", proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b"))],
    )
    data = json_convert(t)
    t2 = Tag(**r_recover(data))
    assert t.raw == t2.raw
    assert t == t2

def test_proto_creator():
    Creator = proto.Creator
    c = Creator("test", avatar=proto.Source(proto.Source.types.bin, ''), _id=proto.UID(),
    pixiv=proto.Pixiv(12345, 6676),
    homepage="127.0.0.1",
    )
    data = json_convert(c)
    c2 = Creator(**r_recover(data))
    assert c.raw == c2.raw
    assert c == c2

@pytest.mark.asyncio
async def test_tinyend():
    # Test consistency of UID
    assert isinstance(tinyend.UID("5f9f1b9b4b9b9b9b9b9b9b9b"), proto.UID)
    assert tinyend.UID("5f9f1b9b4b9b9b9b9b9b9b9b") == tinyend.UID("5f9f1b9b4b9b9b9b9b9b9b9b")
    assert tinyend.UID("5f9f1b9b4b9b9b9b9b9b9b9b") == proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b")
    assert hash(tinyend.UID("5f9f1b9b4b9b9b9b9b9b9b9b")) == hash(proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b"))
    assert hash(tinyend.UID(tinyend.UID("5f9f1b9b4b9b9b9b9b9b9b9b"))) == hash(proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b"))
    assert hash(tinyend.UID(proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b"))) == hash(proto.UID("5f9f1b9b4b9b9b9b9b9b9b9b"))

    # Test invalid type
    with pytest.raises(TypeError):
        tinyend.UID(12345)
