import datetime

import pytest

from blob.models import Blob  # isort:skip
from collection.models import Collection  # isort:skip

pytestmark = pytest.mark.django_db


def test_sort_collection(collection):

    collection.sort(1000, 2)
    assert collection.blob_list[0]["id"] == 2000
    assert collection.blob_list[1]["id"] == 1000
    assert len(collection.blob_list) == 2

    collection.sort(2000, 1)
    assert collection.blob_list[0]["id"] == 2000
    assert collection.blob_list[1]["id"] == 1000
    assert len(collection.blob_list) == 2

    collection.sort(1000, 1)
    assert collection.blob_list[0]["id"] == 1000
    assert collection.blob_list[1]["id"] == 2000
    assert len(collection.blob_list) == 2

    # Test that specifying an invalid blob id raises an exception
    with pytest.raises(ValueError):
        collection.sort(1, 1)


def test_get_tags(collection):

    # Use set() since get_tags() doesn't guarantee sort order
    assert set([x.strip() for x in collection.get_tags().split(",")]) == set(["django", "linux"])


def test_get_blob(collection):

    assert collection.get_blob(-1) == {}
    assert collection.get_blob(0)["blob_id"] == 1000
    assert collection.get_blob(1)["blob_id"] == 2000
    assert collection.get_blob(3) == {}
