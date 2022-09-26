"""Modified from bson/json_util.py"""
# Copyright 2009-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import datetime
import uuid
from typing import Any
from bson.dbref import DBRef
from bson.objectid import ObjectId

def json_convert(obj: Any, memo: dict[int, Any]=None) -> Any:
    """Recursive helper method that converts extended types so they can be
    converted into json.
    """
    if memo is None:
        memo = {}
    _id = id(obj)
    if _id in memo:
        return memo[_id]
    if hasattr(obj, "items"):
        dummyd: dict[str, Any] = {}
        memo[_id] = dummyd  # So we don't recurse infinitely
        dummyd.update((k, json_convert(v, memo)) for k, v in obj.items())
        return dummyd
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        dummyl: list[Any] = []
        memo[_id] = dummyl  # So we don't recurse infinitely
        dummyl.extend((json_convert(v, memo) for v in obj))
        return dummyl
    try:
        ret = convert(obj)
        memo[_id] = ret
        return ret
    except TypeError:
        return obj

def r_recover(obj: Any) -> Any:
    """Recursively recover extended types."""
    if isinstance(obj, list):
        return list((r_recover(v) for v in obj))
    if isinstance(obj, dict):
        rec = {k: r_recover(v) for k, v in obj.items()}
        return recover(rec)
    return obj

def convert(obj: Any) -> Any:
    # We preserve key order when rendering SON, DBRef, etc. as JSON by
    # returning a SON for those types instead of a dict.
    if isinstance(obj, ObjectId):
        return {"$oid": str(obj)}
    if isinstance(obj, DBRef):
        return json_convert(obj.as_doc())
    if isinstance(obj, datetime.datetime):
        return {"$date": obj.isoformat()}
    if isinstance(obj, bytes):
        return _encode_binary(obj)
    if isinstance(obj, uuid.UUID):
        return {"$uuid": obj.hex}
    raise TypeError(f"Not in converting list: {obj}")

def recover(dct: dict[str, Any]) -> Any:
    if "$oid" in dct:
        return _parse_canonical_oid(dct)
    if (
        isinstance(dct.get("$ref"), str)
        and "$id" in dct
        and isinstance(dct.get("$db"), (str, type(None)))
    ):
        return _parse_canonical_dbref(dct)
    if "$date" in dct:
        return _parse_datetime(dct)
    if "$binary" in dct:
        return _parse_binary(dct)
    if "$uuid" in dct:
        return _parse_uuid(dct)
    return dct

def _parse_uuid(doc: Any) -> uuid.UUID:
    """Decode a JSON $uuid to Python UUID."""
    if len(doc) != 1:
        raise TypeError("Bad $uuid, extra field(s): %s" % (doc,))
    if not isinstance(doc["$uuid"], str):
        raise TypeError("$uuid must be a string: %s" % (doc,))
    return uuid.UUID(doc["$uuid"])

def _parse_binary(doc: Any) -> bytes:
    b64 = doc["$binary"]
    if not isinstance(b64, str):
        raise TypeError("$binary base64 must be a string: %s" % (doc,))

    return base64.b64decode(b64.encode())

def _parse_datetime(doc: Any) -> datetime.datetime:
    """Decode a JSON datetime to python datetime.datetime."""
    dtm = doc["$date"]
    if len(doc) != 1:
        raise TypeError("Bad $date, extra field(s): %s" % (doc,))
    
    return datetime.datetime.fromisoformat(dtm)

def _parse_canonical_oid(doc: Any) -> ObjectId:
    """Decode a JSON ObjectId to bson.objectid.ObjectId."""
    if len(doc) != 1:
        raise TypeError("Bad $oid, extra field(s): %s" % (doc,))
    return ObjectId(doc["$oid"])

def _parse_canonical_dbref(doc: Any) -> DBRef:
    """Decode a JSON DBRef to bson.dbref.DBRef."""
    return DBRef(doc.pop("$ref"), doc.pop("$id"), database=doc.pop("$db", None), **doc)

def _encode_binary(data: bytes) -> Any:
    return {"$binary": base64.b64encode(data).decode()}
