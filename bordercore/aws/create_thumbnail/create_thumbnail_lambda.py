"""
Sequence of events when this lambda gets triggered:

The S3 object which triggered the lambda gets downloaded from S3
and into the /tmp directory of the lambda runtime environment. So
if the original file is called foo.pdf, then it will be downloaded
to this location:

/tmp/blobs/<uuid>-foo.pdf, eg:

/tmp/blobs/b305e9fd-32cb-4c5d-be6f-ad75910e38d8-foo.pdf

For pdfs, one page is extracted and saved. Eg, if the first page
(the default) is specified, then the filename looks like this:

/tmp/blobs/<uuid>-foo_p0.pdf

Then this page is converted into a large and small cover images
and stored here:

/tmp/covers/<uuid>-cover.jpg
/tmp/covers/<uuid>-cover-large.jpg

If the original uploaded file is an image, then its cover image will
be created here:

/tmp/covers/<uuid>-cover.jpg

Its width and height dimensions are calculated and stored as S3 metadata.

All cover images are then uploaded to S3 in the same directory
as the original file.

For bookmarks, only a small cover image is created, since the Chromda lambda
generates the large version based on the bookmark's webpage.
"""

import glob
import json
import logging
import os
import re
from pathlib import PurePath
from urllib.parse import unquote_plus

import boto3
from PIL import Image

from lib.thumbnails import create_thumbnail

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")
EFS_DIR = os.environ.get("EFS_DIR", "/tmp")
BLOBS_DIR = f"{EFS_DIR}/blobs"
COVERS_DIR = f"{EFS_DIR}/covers"


def is_cover_image(bucket, key):
    """
    Cover images have metadata "cover-image" set to "Yes"
    """
    response = s3_client.head_object(Bucket=bucket, Key=key)

    return response["Metadata"].get("cover-image", None) == "Yes"


def extract_uuid(key):
    # UUID format: 8-4-4-4-12 hexadecimal digits
    uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    match = re.search(uuid_pattern, key)
    if match:
        return match.group()
    else:
        raise ValueError(f"Can't extract uuid from key: {key}")


def get_cover_filename(key, uuid, is_bookmark):
    """
    For blobs, the filename is cover.jpg or cover-large.jpg.
    For bookmarks, the filename is <uuid>-small.png.
    """

    if is_bookmark:
        cover_filename = f"{uuid}-small.png"
    else:
        _, cover_filename = key.split(f"{COVERS_DIR}/{uuid}-")

    return cover_filename


def handler(event, context):

    try:

        for record in event["Records"]:
            log.info(json.dumps(record["Sns"]["Message"]))
            sns_record = json.loads(record["Sns"]["Message"])["Records"][0]
            bucket = sns_record["s3"]["bucket"]["name"]

            # Ignore object delete events
            if sns_record["eventName"] == "ObjectRemoved:Delete":
                continue

            # Spaces are replaced with "+"s
            key = unquote_plus(sns_record["s3"]["object"]["key"])

            is_bookmark = key.startswith("bookmarks/")

            # Look for an optional page number (for pdfs)
            page_number = sns_record["s3"]["object"].get("page_number", 1)

            log.info(f"Creating cover image for {key}")

            p = PurePath(key)
            path = p.parent
            filename = p.name

            if is_cover_image(bucket, key):
                log.info(f"Skipping cover image {filename}")
                continue

            uuid = extract_uuid(key)

            try:
                os.mkdir(BLOBS_DIR)
            except FileExistsError:
                pass

            try:
                os.mkdir(COVERS_DIR)
            except FileExistsError:
                pass

            download_path = f"{BLOBS_DIR}/{uuid}-{filename}"

            s3_client.download_file(bucket, key, download_path)
            create_thumbnail(download_path, f"{COVERS_DIR}/{uuid}", page_number)

            # Upload all cover images created (large or small) to S3
            for cover in glob.glob(f"{COVERS_DIR}/{uuid}-cover*"):
                width, height = Image.open(cover).size
                cover_filename = get_cover_filename(cover, uuid, is_bookmark)
                log.info(f"coverfile: {cover_filename}")
                s3_client.upload_file(
                    cover,
                    bucket,
                    f"{path}/{cover_filename}",
                    ExtraArgs={"Metadata": {"image-width": str(width),
                                            "image-height": str(height),
                                            "cover-image": "Yes"},
                               "ContentType": "image/jpeg"}
                )
                os.remove(cover)

            os.remove(download_path)

    except Exception as e:
        import traceback
        log.info(traceback.print_exc())
        log.error(f"Lambda Exception: {e}")
