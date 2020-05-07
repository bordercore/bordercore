# Sample script demonstrating how to rename objects in S3

import re

import boto3
from boto3 import client

import django
from django.conf import settings

django.setup()

bucket_name = "bordercore-blobs"

s3_client = client("s3")
s3_resource = boto3.resource("s3")

paginator = s3_client.get_paginator("list_objects")
page_iterator = paginator.paginate(Bucket=bucket_name)

for page in page_iterator:

    for key in page["Contents"]:

        # blobs/f7/f7a63e40b2c4cc095dab6279caf4a6959e542e2f/cover
        p = re.compile(r"^blobs/\w{2}/\w{40}/cover-small.jpg")

        if p.match(str(key["Key"])):

            new_key = key["Key"].replace("cover-small.jpg", "cover.jpg")

            print(key["Key"])
            print(new_key)
            print(f"{settings.AWS_STORAGE_BUCKET_NAME}/{key['Key']}")

            s3_resource.Object(settings.AWS_STORAGE_BUCKET_NAME, new_key).copy_from(CopySource=f"{settings.AWS_STORAGE_BUCKET_NAME}/{key['Key']}")
            s3_resource.Object(settings.AWS_STORAGE_BUCKET_NAME, key["Key"]).delete()
