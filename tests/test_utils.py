import pytest
import tempfile
import os
import ujson as json
from uuid import uuid4
from typing import AnyStr
from datetime import datetime, timezone
from utils import merge_ancestors

def test_merge_ancestors():
    ls = [
        [1,2,4,5,6],
        [1,6],
        [1,3,5]
    ]
    assert merge_ancestors(ls) == [[1,3,5],[1,2,4,5,6]]
    ls = [
        [1,2, 3,5,6,7],
        [1,6,8]
    ]
    assert merge_ancestors(ls) == [[1,6,8],[1,2,3,5,6,7]]