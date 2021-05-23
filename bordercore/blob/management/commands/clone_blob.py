# Create a copy of a blob, including its metadata.
#  Does not include the file, if present.
#  Optionally add it to a collection.

import datetime

from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from blob.models import Blob, MetaData
from collection.models import Collection


class Command(BaseCommand):
    help = "Clone a blob"

    def add_arguments(self, parser):
        parser.add_argument(
            "--uuid",
            help="The UUID of the blob to clone",
            required=True
        )
        parser.add_argument(
            "--collection-uuid",
            help="The UUID of the collection to which the blob belongs",
        )

    @atomic
    def handle(self, *args, uuid, collection_uuid, **kwargs):

        original_blob = Blob.objects.get(uuid=uuid)
        print(f"Cloning blob named '{original_blob.name}'")

        new_blob = Blob.objects.create(
            content=original_blob.content,
            name=f"Copy of {original_blob.name}",
            user=original_blob.user,
            date=original_blob.date,
            importance=original_blob.importance,
            is_private=original_blob.is_private,
            is_note=original_blob.is_note
        )

        print(f"New blob uuid: {new_blob.uuid}")

        for x in original_blob.metadata_set.all():
            MetaData.objects.create(
                user=original_blob.user,
                name=x.name,
                value=x.value,
                blob=new_blob)

        for x in original_blob.tags.all():
            new_blob.tags.add(x)

        if collection_uuid:
            collection = Collection.objects.get(user=original_blob.user, uuid=collection_uuid)
            blob_info = {
                "id": new_blob.id,
                "added": int(datetime.datetime.now().strftime("%s"))
            }
            collection.blob_list.append(blob_info)
            collection.save()

        # Add to Elasticsearch
        new_blob.index_blob()
