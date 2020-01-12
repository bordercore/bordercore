import glob
import os

import boto3
from botocore.errorfactory import ClientError
import django
from django.db.models import Q
from django.conf import settings

django.setup()

from blob.models import Document
from blob.models import set_s3_metadata_file_modified

walk_dir = "/home/media/blobs"

s3_client = boto3.client("s3")

bucket_name = settings.AWS_STORAGE_BUCKET_NAME

for blob in Document.objects.filter(~Q(file="")).order_by('?'):

    # blob = Document.objects.get(sha1sum="6e0b5097b0925c6d9944f1c37c74d3a290a1e38b")

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
