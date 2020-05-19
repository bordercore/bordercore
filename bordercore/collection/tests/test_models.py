import datetime

import django

from .factories import CollectionFactory

django.setup()

from blob.models import Document  # isort:skip
from collection.models import Collection  # isort:skip


def test_sort_collection(user):

    collection = CollectionFactory()

    collection.sort(1, 2)
    assert collection.blob_list[0]["id"] == 2
    assert collection.blob_list[1]["id"] == 1
    assert collection.blob_list[2]["id"] == 3
    assert len(collection.blob_list) == 3

    collection.sort(3, 2)
    assert collection.blob_list[0]["id"] == 2
    assert collection.blob_list[1]["id"] == 3
    assert collection.blob_list[2]["id"] == 1
    assert len(collection.blob_list) == 3

    collection.sort(1, 1)
    assert collection.blob_list[0]["id"] == 1
    assert collection.blob_list[1]["id"] == 2
    assert collection.blob_list[2]["id"] == 3
    assert len(collection.blob_list) == 3


def test_get_created(collection):

    assert collection.get_created() == datetime.datetime.now().strftime('%b %d, %Y')


def test_get_tags(collection):

    assert collection.get_tags() == "django, linux"


def test_get_blob(collection):

    assert collection.get_blob(-1) == {}
    assert collection.get_blob(0)["blob_id"] == 1
    assert collection.get_blob(1)["blob_id"] == 2
    assert collection.get_blob(2)["blob_id"] == 3
    assert collection.get_blob(3) == {}
