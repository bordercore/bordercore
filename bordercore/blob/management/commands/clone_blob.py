# Create a copy of a blob, including its metadata.
#  Does not include the file, if present.
#  Optionally add it to a collection.

from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from blob.models import Blob, MetaData


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
        self.stdout.write(f"Cloning blob named '{original_blob.name}'")

        new_blob = Blob.objects.create(
            content=original_blob.content,
            name=f"Copy of {original_blob.name}",
            user=original_blob.user,
            date=original_blob.date,
            importance=original_blob.importance,
            is_private=original_blob.is_private,
            is_note=original_blob.is_note
        )

        self.stdout.write(f"New blob uuid: {new_blob.uuid}")

        for x in original_blob.metadata_set.all():
            MetaData.objects.create(
                user=original_blob.user,
                name=x.name,
                value=x.value,
                blob=new_blob)

        for x in original_blob.tags.all():
            new_blob.tags.add(x)

        if collection_uuid:
            new_blob.add_to_collection(original_blob.user, collection_uuid)

        # Add to Elasticsearch
        new_blob.index_blob()
