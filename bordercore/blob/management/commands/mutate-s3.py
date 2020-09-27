# Sample script showing how to perform some action on objects in S3
#  that match a regex.

import re

import boto3
from boto3 import client

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic


class Command(BaseCommand):
    help = "Add metadata to S3 blob objects"

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def add_arguments(self, parser):
        parser.add_argument(
            "--action",
            choices=["add_metadata", "rename"],
            required=True,
            help="The action to take",
        )

    def action_rename(self, key):
        #  Rename all matched objects to "cover.jpg"

        new_key = key["Key"].replace("cover-small.jpg", "cover.jpg")

        self.s3_resource.Object(settings.AWS_STORAGE_BUCKET_NAME, new_key).copy_from(CopySource=f"{settings.AWS_STORAGE_BUCKET_NAME}/{key['Key']}")
        self.s3_resource.Object(settings.AWS_STORAGE_BUCKET_NAME, key["Key"]).delete()

    def action_add_metadata(self, key):
        #  Add the key-value pair ("cover-image", "Yes") to all matched
        #    objects which have the filename "cover-small.jpg"

        response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key["Key"])

        if response["Metadata"].get("cover-image", None) == "Yes":
            self.stdout.write(" metadata already found. Skipping")
        else:
            self.stdout.write(" Adding metadata")
            s3_object = self.s3_resource.Object(self.bucket_name, key["Key"])
            s3_object.metadata.update({"cover-image": "Yes"})
            s3_object.copy_from(
                CopySource={"Bucket": self.bucket_name, "Key": key["Key"]},
                Metadata=s3_object.metadata, MetadataDirective="REPLACE")

    @atomic
    def handle(self, action, *args, **kwargs):

        self.s3_client = client("s3")
        self.s3_resource = boto3.resource("s3")

        paginator = self.s3_client.get_paginator("list_objects")
        page_iterator = paginator.paginate(Bucket=self.bucket_name)

        for page in page_iterator:

            for key in page["Contents"]:

                # blobs/f7/f7a63e40b2c4cc095dab6279caf4a6959e542e2f/cover
                p = re.compile(r"^blobs/\w{2}/\w{40}/cover-small.jpg")
                if p.match(str(key["Key"])):

                    self.stdout.write(key["Key"])

                    if action == "rename":
                        self.action_rename(key)
                    elif action == "add_metadata":
                        self.action_add_metadata(key)
