import datetime

import pytest

import django

django.setup()

from django.contrib.auth.models import User  # isort:skip
from collection.models import Collection  # isort:skip
from blob.models import Blob  # isort:skip
from tag.models import Tag  # isort:skip


@pytest.fixture(scope="function")
def collection(user):

    blobs = [
        Blob.objects.create(
            id=1,
            user=user),
        Blob.objects.create(
            id=2,
            user=user),
        Blob.objects.create(
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

    tag1, created = Tag.objects.get_or_create(name="django")
    tag2, created = Tag.objects.get_or_create(name="linux")
    collection.tags.add(tag1, tag2)

    yield collection
