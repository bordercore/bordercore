import logging
import os
from pathlib import PurePath
from urllib.parse import unquote_plus

import boto3
from PIL import Image

from lib.thumbnails import create_bookmark_thumbnail

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

s3_client = boto3.client("s3")

EFS_DIR = os.environ.get("EFS_DIR", "/tmp") + "/bookmarks"


def is_cover_image(bucket, key):
    """
    Cover images have metadata "cover-image" set to "Yes"
    """
    response = s3_client.head_object(Bucket=bucket, Key=key)

    return response["Metadata"].get("cover-image", None) == "Yes"


def handler(event, context):

    try:

        for record in event["Records"]:
            bucket = record["s3"]["bucket"]["name"]

            # Ignore object delete events
            if record["eventName"] == "ObjectRemoved:Delete":
                continue

            # Spaces are replaced with '+'s
            key = unquote_plus(record["s3"]["object"]["key"])

            log.info(f"Creating thumbnail image for {key}")

            p = PurePath(key)
            path = p.parent
            filename = p.name

            if is_cover_image(bucket, key):
                log.info(f"Skipping cover image {filename}")
                continue

            download_path = f"{EFS_DIR}/{filename}"
            s3_client.download_file(bucket, key, download_path)

            thumbnail_filename = f"{p.stem}-small.png"
            thumbnail_filepath = f"{EFS_DIR}/{thumbnail_filename}"
            create_bookmark_thumbnail(download_path, thumbnail_filepath)

            # Upload all cover images created (large or small) to S3
            width, height = Image.open(thumbnail_filepath).size
            s3_client.upload_file(
                thumbnail_filepath,
                bucket,
                f"{path}/{thumbnail_filename}",
                ExtraArgs={
                    'Metadata': {
                        "image-width": str(width),
                        "image-height": str(height),
                        "cover-image": "Yes"
                    },
                    "ContentType": "image/png"
                }
            )

            os.remove(thumbnail_filepath)
            os.remove(download_path)

    except Exception as e:
        import traceback
        log.info(traceback.print_exc())
        log.error(f"Lambda Exception: {e}")
