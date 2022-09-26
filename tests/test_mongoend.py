from library import mongoend as td
from library.tinyend import Pixiv
from utils import real_path
import pymongo as mongo
import pytest
import tempfile
import asyncio
import os

@pytest.mark.asyncio
async def test_mongoend():
    murl = "mongodb://localhost:27017/test"
    lib = td.Library(murl)

    tag1_id = await lib.Tags.new_uid()
    p1_id = await lib.Pictures.new_uid()
    c1_id = await lib.Creators.new_uid()
    a1_id = await lib.Albums.new_uid()
    col1_id = await lib.Collections.new_uid()
    b1_id = await lib.Binaries.new_uid()

    tag1 = td.Tag(lib, "tag1", _id=tag1_id)

    p1 = td.Picture(lib, "pic1", td.Picture.types.illust, td.CreatorRef("AR1"),_id=p1_id,
        caption="Test caption", tags=[tag1.name], pixiv=td.Pixiv(123,456,0), 
        frame_info=td.FrameInfo(title="test",order=0, id=td.proto.UID(), duration=50.0),
        src=[td.Source("url", "https://example.com")], dims=td.Dimensions(100,200), 
        geo=td.Geo("Point", [12,34]))

    c1 = td.Creator(lib, "creator1", c1_id)
    a1 = td.Album(lib, "album1", td.Album.types.picture, [], _id=a1_id, pixiv=Pixiv(123,456,0))
    col1 = td.Collection(lib, "collection1", td.Collection.types.general, _id=col1_id)
    b1 = td.Binary(lib, "binary1", td.Binary.types.image, b"szivcsif1", _id=b1_id)
    c1.avatar.value = await b1.ref_from(c1)
    await a1.flush()
    await c1.flush()
    await p1.flush()
    await p1.retrieve()
    assert p1.pixiv.pid == 123
    assert p1.src[0].value == "https://example.com"
    await tag1.flush()
    await tag1.add_member(p1)
    await p1.bind_creator(c1)
    await p1.join_album(a1)
    await col1.add_member(p1)
    await p1.flush()
    await tag1.flush()
    await a1.flush()
    assert p1._id in a1.members
    assert td.DBRef("Pictures", p1._id) in tag1.members
    assert p1.creator.name == c1.name
    assert p1.creator.id == c1._id
    await lib.Binaries.delete(b1._id)
    await p1.retrieve()
    await a1.retrieve()
    print(lib, end='')
    await lib.close()
    lib2 = td.Library(murl)
    pp1 = await lib2.Pictures.get(p1._id)
    aa1 = await lib2.Albums.get_by_pid(p1.pixiv.pid)
    assert pp1 == p1
    assert aa1 == a1

