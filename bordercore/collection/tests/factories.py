import datetime

import factory

from django.contrib.auth.models import User
from django.db.models import signals

from blob.models import Document
from collection.models import Collection


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = "testuser"


class CollectionFactory(factory.DjangoModelFactory):

    class Meta:
        model = Collection

    name = factory.Sequence(lambda n: f"collection_{n}")
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def create_blobs(obj, create, extracted, **kwargs):

        if not create:
            return

        blobs = [
            Document.objects.create(
                id=1,
                user=obj.user),
            Document.objects.create(
                id=2,
                user=obj.user),
            Document.objects.create(
                id=3,
                user=obj.user)
        ]
        obj.blob_list = [
            {
                "id": x.id,
                "added": int(datetime.datetime.now().strftime("%s"))
            }
            for x in blobs
        ]
