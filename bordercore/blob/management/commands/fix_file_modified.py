# If a blob's modification date on filesystem doesn't match its
#  S3 metadata, fix it. You can optionally pass in a modtime from
#  the command line to manually set it.

import os

import boto3

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.db.transaction import atomic

from blob.models import Blob, set_s3_metadata_file_modified


class Command(BaseCommand):
    help = "Set a blob's file modified S3 metadata"

    BLOB_DIR = "/home/media"
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def add_arguments(self, parser):
        parser.add_argument(
            "--uuid",
            help="The UUID of the blob to modify",
        )
        parser.add_argument(
            "--modified-time",
            help="The timestamp to set for 'modified'",
        )
        parser.add_argument(
            "--dry-run",
            help="Dry run. Take no action",
            action="store_true"
        )
        parser.add_argument(
            "--verbose",
            help="Increase verbosity",
            action="store_true"
        )

    @atomic
    def handle(self, *args, uuid, modified_time, dry_run, verbose, **kwargs):

        if modified_time and not uuid:
            raise CommandError("If you specify a modified_time, you must also specify a uuid")

        if uuid:
            # A single blob
            blobs = Blob.objects.filter(uuid=uuid)
        else:
            # All blobs
            blobs = Blob.objects.filter(~Q(file="")).order_by("created")

        for blob_info in blobs:

            key = blob_info.s3_key
            file_path = f"{self.BLOB_DIR}/{key}"

            if verbose:
                self.stdout.write(f"{blob_info} file_path={file_path}")

            s3_resource = boto3.resource("s3")

            if os.path.isfile(file_path):
                obj = s3_resource.Object(bucket_name=self.bucket_name, key=key)
                modified_time_s3 = obj.metadata.get("file-modified", None)

                # If the modtime wasn't specified, use the file's current modtime
                if not modified_time:
                    modified_time_file = int(os.stat(file_path).st_mtime)

                if not modified_time_s3 or modified_time_s3 == "None" or modified_time_file != int(modified_time_s3):
                    self.stdout.write(f"{blob_info.uuid} File modification timestamp does not match. Fixing. mtime_s3={modified_time_s3}, mtime_file={modified_time_file}")
                    if not dry_run:
                        blob_info.file_modified = modified_time_file
                        set_s3_metadata_file_modified(None, blob_info)
                elif verbose:
                    self.stdout.write(self.style.WARNING(f"{blob_info.uuid} S3 file modification timestamp exists and matches filesystem. Nothing to do."))

            else:
                raise CommandError(f"{blob_info.uuid} File not found on file system: {file_path}")
