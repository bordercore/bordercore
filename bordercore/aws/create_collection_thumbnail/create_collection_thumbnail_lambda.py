import json
import logging
import os
import subprocess

import boto3
import requests

# from requests_aws4auth import AWS4Auth

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)

EFS_DIR = os.environ.get("EFS_DIR", "/tmp")
DRF_TOKEN = os.environ.get("DRF_TOKEN")
S3_BUCKET_NAME = "bordercore-blobs"

# credentials = boto3.Session().get_credentials()
# awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, os.environ["AWS_REGION"], "es", session_token=credentials.token)

s3_client = boto3.client("s3")


def download_images_from_collection(collection_uuid):

    headers = {"Authorization": f"Token {DRF_TOKEN}"}
    r = requests.get(f"https://www.bordercore.com/api/collections/images/{collection_uuid}/", headers=headers)
    if r.status_code != 200:
        raise Exception(f"Error: status code: {r.status_code}")

    blob_list = r.json()
    log.info(blob_list)

    filenames = []

    for blob in blob_list:

        if blob["filename"].endswith("pdf"):
            # For pdfs, download the cover image
            s3_key = "cover-large.jpg"
        else:
            # For images, download the image itself
            s3_key = blob["filename"]

        # Prepend the blob's uuid to insure uniqueness
        filename = f"{blob['uuid']}-{s3_key}"
        filenames.append(filename)

        file_path = f"{EFS_DIR}/collections/{filename}"
        s3_client.download_file(S3_BUCKET_NAME, f"blobs/{blob['uuid']}/{s3_key}", file_path)

    return filenames


def handler(event, context):

    try:

        for record in event["Records"]:

            sns_record = json.loads(record["Sns"]["Message"])["Records"][0]

            collection_uuid = sns_record["s3"].get("collection_uuid")

            log.info(f"Creating cover image for collection_uuid: {collection_uuid}")

            thumbnail_filename = f"{collection_uuid}.jpg"

            blob_list = download_images_from_collection(collection_uuid)

            if blob_list:
                result = subprocess.run(
                    [
                        "sh",
                        f"{EFS_DIR}/create-cover.sh",
                        collection_uuid,
                        *blob_list
                    ],
                    capture_output=True
                )

                log.info(f"create-cover.sh result: {result}")

                # Upload the resulting thumbnail back to S3
                # width, height = Image.open(cover).size
                s3_client.upload_file(
                    f"{EFS_DIR}/collections/{thumbnail_filename}",
                    S3_BUCKET_NAME,
                    f"collections/{thumbnail_filename}",
                    ExtraArgs={"ContentType": "image/jpeg"}
                )

                # Delete the sample images once done
                for blob in blob_list:
                    os.remove(f"{EFS_DIR}/collections/{blob}")

                os.remove(f"{EFS_DIR}/collections/{thumbnail_filename}")

        log.info("Lambda finished")

    except Exception as e:
        log.error(f"{type(e)} exception: {e}")
        log.error(sns_record)
        import traceback
        print(traceback.format_exc())
