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
            "--include-collections",
            action="store_true",
            help="Add the cloned blob to the same collections as the original",
        )

    @atomic
    def handle(self, *args, uuid, collection_uuid, **kwargs):

        original_blob = Blob.objects.get(uuid=uuid)
        self.stdout.write(f"Cloning blob named '{original_blob.name}'")

        original_blob.clone(include_collections)
