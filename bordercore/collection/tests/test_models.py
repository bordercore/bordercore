import datetime

import django

django.setup()

# from django.contrib.auth.models import User  # isort:skip
from blob.models import Document  # isort:skip
from collection.models import Collection  # isort:skip


def test_sort_collection(user):

    blobs = [
        Document.objects.create(
            id=1,
            user=user),
        Document.objects.create(
            id=2,
            user=user),
        Document.objects.create(
            id=3,
            user=user)
    ]

    collection = Collection.objects.create(
        blob_list=[
            {
                "id": x.id,
                "added": int(datetime.datetime.now().strftime("%s"))
            }
            for x in blobs
        ],
        user=user
    )

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
