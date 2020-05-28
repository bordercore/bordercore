import json
import logging
import os

import boto3

import django
from django.conf import settings

# Only call django.setup() when called from a command-line
# script, ie outside the context of Django. Without this Django
# throws a "RuntimeError: populate() isn't reentrant" error
if not hasattr(django, "apps"):
    django.setup()

from blob.models import Blob  # isort:skip

BLOB_DIR = "/home/media"
bucket_name = settings.AWS_STORAGE_BUCKET_NAME

logger = logging.getLogger("bordercore.admin")


def fix_file_modified(uuid, force=True):

    if uuid is None:
        raise Exception("Please specify the uuid")

    blob = Blob.objects.get(uuid=uuid)
    key = blob.get_s3_key()
    file_path = f"{BLOB_DIR}/{key}"

    logger.info(f"{uuid} file_path={file_path}")

    s3_resource = boto3.resource("s3")

    if os.path.isfile(file_path):
        obj = s3_resource.Object(bucket_name=bucket_name, key=key)
        s3_modified = obj.metadata.get("file-modified", None)
        file_modified = int(os.stat(file_path).st_mtime)
        if not s3_modified or file_modified != int(s3_modified):
            logger.info(f"{uuid} File mod time does not match. Fixing. s3_modified={s3_modified}, file modified={file_modified}")
            obj.metadata.update({"file-modified": str(file_modified)})
            obj.copy_from(CopySource={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key}, Metadata=obj.metadata, MetadataDirective="REPLACE")
        else:
            logger.warn("File modification timestamp exists and matches filesystem. Nothing to do.")
    else:
        logger.error(f"File not found on file system: {file_path}")


def get_s3_metadata(sha1sum, uuid):

    s3 = boto3.resource("s3")

    if not uuid and not sha1sum:
        raise Exception("Specify the sha1sum or uuid")
    elif uuid and sha1sum:
        raise Exception("You must not specify both the sha1sum and uuid")
    elif uuid:
        kwargs = {"uuid": uuid}
    elif sha1sum:
        kwargs = {"sha1sum": sha1sum}

    b = Blob.objects.get(**kwargs)

    obj = s3.Object(bucket_name='bordercore-blobs', key=b.get_s3_key())

    logger.info(json.dumps(obj.metadata))
