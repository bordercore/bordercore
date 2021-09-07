# Get S3 metadata for a blob

import json

import boto3

from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic

from blob.models import Blob


class Command(BaseCommand):
    help = "Get S3 metadata for a blob"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sha1sum",
            help="The sha1sum of the blob",
        )
        parser.add_argument(
            "--uuid",
            help="The UUID of the blob",
        )

    @atomic
    def handle(self, *args, sha1sum, uuid, **kwargs):

        s3 = boto3.resource("s3")

        if not uuid and not sha1sum:
            raise CommandError("Specify the sha1sum or uuid")
        elif uuid and sha1sum:
            raise CommandError("You must not specify both the sha1sum and uuid")
        elif uuid:
            kwargs = {"uuid": uuid}
        elif sha1sum:
            kwargs = {"sha1sum": sha1sum}

        b = Blob.objects.get(**kwargs)

        obj = s3.Object(bucket_name="bordercore-blobs", key=b.s3_key)

        self.stdout.write(json.dumps(obj.metadata))
