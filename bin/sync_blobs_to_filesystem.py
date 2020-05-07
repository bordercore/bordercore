# Iterator through all S3 blobs, downloading any to the local filesystem which don't exist

import os
import re
from os import makedirs

import boto3

import django
from django.conf import settings

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
django.setup()

from blob.models import ILLEGAL_FILENAMES  # isort:skip


BLOB_DIR = "/home/media"

bucket_name = settings.AWS_STORAGE_BUCKET_NAME

s3_resource = boto3.resource("s3")

paginator = s3_resource.meta.client.get_paginator("list_objects")
page_iterator = paginator.paginate(Bucket=bucket_name)

for page in page_iterator:

    for key in page["Contents"]:
        m = re.search(r"^(blobs/\w{2}/\w{40})/(.+)", str(key["Key"]))

        if m:
            file_path = f"{BLOB_DIR}/{key['Key']}"
            dirs = m.group(1)
            filename = m.group(2)

            # First check if it already exists
            if not os.path.isfile(file_path) and filename not in ILLEGAL_FILENAMES:
                print(key["Key"])
                makedirs(f"{BLOB_DIR}/{dirs}", exist_ok=True)
                s3_resource.meta.client.download_file(bucket_name, key["Key"], file_path)

                # Set the "modified" timestamp
                obj = s3_resource.Object(bucket_name=bucket_name, key=key["Key"])
                s3_modified = int(obj.metadata["file-modified"])

                # modified = time.mktime(key["LastModified"].timetuple())
                os.utime(file_path, (s3_modified, s3_modified))

            # Temp code to fix modtimes
            if os.path.isfile(file_path) and filename not in ILLEGAL_FILENAMES:
                obj = s3_resource.Object(bucket_name=bucket_name, key=key["Key"])
                s3_modified = int(obj.metadata["file-modified"])
                stat = os.stat(file_path)
                file_modified = int(stat.st_mtime)
                if file_modified != s3_modified:
                    print(f"Does not match: {file_path}")
                    print(f"s3_modifed: {s3_modified}")
                    print(f"file modified: {file_modified}")
                    if len(str(s3_modified)) == 13:
                        s3_modified = int(s3_modified / 1000)
                        obj.metadata.update({"file-modified": str(s3_modified)})
                        obj.copy_from(CopySource={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key["Key"]}, Metadata=obj.metadata, MetadataDirective="REPLACE")
                        os.utime(file_path, (int(obj.metadata["file-modified"]), int(obj.metadata["file-modified"])))
                    else:
                        print("Can't fix automatically. Manual intervention required")
