import glob
import os

import boto3
from botocore.errorfactory import ClientError

import django
from django.conf import settings
from django.db.models import Q

from blob.models import Blob, set_s3_metadata_file_modified

django.setup()


walk_dir = "/home/media/blobs"

s3_client = boto3.client("s3")

bucket_name = settings.AWS_STORAGE_BUCKET_NAME

for blob in Blob.objects.filter(~Q(file="")).order_by('?'):

    if blob.file == "":
        print(f" Skipping {blob.title}")
        continue
    print(f"Syncing {blob.title}")
    key = f"{settings.MEDIA_ROOT}/{blob.file}"
    print(key)

    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        print("  Skipping. Object already exists in S3")
    except ClientError:
        print(f"  Uploading to S3, uuid={blob.uuid}")
        file_path = f"/home/media/{key}"
        s3_client.upload_file(file_path, bucket_name, key)

        info = os.stat(file_path)
        blob.file_modified = info[8]

        # Set the file modification header
        set_s3_metadata_file_modified(None, blob)

    # break
