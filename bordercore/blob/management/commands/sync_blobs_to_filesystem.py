# Iterate through all S3 blobs, downloading any to the local filesystem which don't exist

import os
import re
from os import makedirs

import boto3

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from blob.models import ILLEGAL_FILENAMES  # isort:skip


class Command(BaseCommand):
    help = "Sync all S3 blobs to the filesystem"

    BLOB_DIR = "/home/media"
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            help="Dry run. Take no action",
            action="store_true"
        )

    @atomic
    def handle(self, *args, dry_run, **kwargs):

        s3_resource = boto3.resource("s3")

        paginator = s3_resource.meta.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=self.bucket_name)

        for page in page_iterator:

            for key in page["Contents"]:
                m = re.search(r"^(blobs/\w{2}/\w{40})/(.+)", str(key["Key"]))

                if m:
                    file_path = f"{self.BLOB_DIR}/{key['Key']}"
                    dirs = m.group(1)
                    filename = m.group(2)

                    # First check if it already exists
                    if not os.path.isfile(file_path) and filename not in ILLEGAL_FILENAMES:
                        self.stdout.write(f"Syncing {key['Key']}")

                        if not dry_run:
                            makedirs(f"{self.BLOB_DIR}/{dirs}", exist_ok=True)
                            s3_resource.meta.client.download_file(self.bucket_name, key["Key"], file_path)

                            # Set the "modified" timestamp
                            obj = s3_resource.Object(bucket_name=self.bucket_name, key=key["Key"])
                            s3_modified = int(obj.metadata["file-modified"])

                            os.utime(file_path, (s3_modified, s3_modified))
