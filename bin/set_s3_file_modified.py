# Set the "file_modified" S3 metadata for a file, either based on
#  a command-line argument or from the modification date obtained
#  from the filesystem.
#
#  First argument (mandatory): uuid
#  Second argument (optional) : the file modification date, in epoch time seconds

import os
import sys
from pathlib import Path

import boto3

import django
from django.conf import settings

from blob.models import Blob, set_s3_metadata_file_modified

django.setup()


walk_dir = "/home/media/blobs"

s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

bucket_name = settings.AWS_STORAGE_BUCKET_NAME

try:
    uuid = sys.argv[1]
except IndexError:
    print("Specify the uuid")
    sys.exit(1)

blob = Blob.objects.get(uuid=uuid)

try:
    file_modified = sys.argv[2]
except IndexError:
    file_path = Path(f"/home/media/{settings.MEDIA_ROOT}/{blob.sha1sum[0:2]}/{blob.sha1sum}/{blob.file}")
    print(file_path)

    if file_path.exists():
        print("Blob found on disk. Updating file_modified based on file timestamp")
        file_modified = os.stat(file_path)[8]
    else:
        print("Blob not found on disk and file_modified not specified. Aborting.")
        sys.exit(1)

blob.file_modified = file_modified

print(f"Setting file_modified = {file_modified}")

# Set the file modification date as S3 metadata
set_s3_metadata_file_modified(None, blob)
