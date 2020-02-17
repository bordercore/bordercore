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

/tmp/covers/<uuid>-cover-small.jpg
/tmp/covers/<uuid>-cover-large.jpg

If the original uploaded file is an image, then its cover image will
be created here:

/tmp/covers/<uuid>-cover.jpg

Its width and height dimensions are calculated and stored as S3 metadata.

All cover images are then uploaded to S3 in the same directory
as the original file.
"""

import boto3
import glob
import json
import logging
import os
from urllib.parse import unquote_plus
import uuid
from PIL import Image

from lib.thumbnails import create_thumbnail, is_image

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

BLOBS_DIR = "/tmp/blobs"
COVERS_DIR = "/tmp/covers"


def set_s3_metadata_image_dimensions(bucket, key, file_path):
    """
    """
    width, height = Image.open(file_path).size

    s3_object = s3_resource.Object(bucket, key)
    s3_object.metadata.update({"image-width": str(width)})
    s3_object.metadata.update({"image-height": str(height)})
    s3_object.copy_from(CopySource={"Bucket": bucket, "Key": key}, Metadata=s3_object.metadata, MetadataDirective="REPLACE")


def is_cover_image(bucket, key):
    """
    Cover images have metadata "cover-image" set to "Yes"
    """
    response = s3_client.head_object(Bucket=bucket, Key=key)

    if response["Metadata"].get("cover-image", None) == "Yes":
        return True
    else:
        return False


def handler(event, context):

    try:

        for record in event["Records"]:
            log.info(json.dumps(record["Sns"]["Message"]))
            sns_record = json.loads(record["Sns"]["Message"])["Records"][0]
            bucket = sns_record["s3"]["bucket"]["name"]

            # Spaces are replaced with '+'s
            key = unquote_plus(sns_record["s3"]["object"]["key"])

            log.info(f"Creating cover image for {key}")

            path, filename = os.path.split(key)

            if is_cover_image(bucket, key):
                log.info(f"Skipping cover image {filename}")
                continue

            myuuid = uuid.uuid4()

            try:
                os.mkdir(BLOBS_DIR)
            except FileExistsError:
                pass

            try:
                os.mkdir(COVERS_DIR)
            except FileExistsError:
                pass

            download_path = f"{BLOBS_DIR}/{myuuid}-{filename}"

            s3_client.download_file(bucket, key, download_path)
            create_thumbnail(download_path, f"{COVERS_DIR}/{myuuid}")

            # Upload all cover images created (large or small) to S3
            for cover in glob.glob(f"{COVERS_DIR}/{myuuid}-cover*"):
                width, height = Image.open(cover).size
                _, coverfile = cover.split(f"{COVERS_DIR}/{myuuid}-")
                s3_client.upload_file(
                    cover,
                    bucket,
                    f"{path}/{coverfile}",
                    ExtraArgs={'Metadata': {"image-width": str(width),
                                            "image-height": str(height),
                                            "cover-image": "Yes"}}
                )
                os.remove(cover)

            # If the object is an image (or is a cover image from the original
            #  object), store its dimensions as S3 metadata
            if is_image(download_path):
                set_s3_metadata_image_dimensions(bucket, key, download_path)

            os.remove(download_path)

    except Exception as e:
        import traceback
        log.info(traceback.print_exc())
        log.error(f"Lambda Exception: {e}")
