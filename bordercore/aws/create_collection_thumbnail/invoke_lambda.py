import argparse
import json
import pprint

import boto3

import django
from django.conf import settings

django.setup()

from blob.models import Blob  # isort:skip

client = boto3.client("lambda")


def invoke(uuid):

    client = boto3.client("sns")

    message = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": settings.AWS_STORAGE_BUCKET_NAME,
                    },
                    "collection_uuid": str(uuid)
                }
            }
        ]
    }

    client.publish(
        TopicArn=settings.CREATE_COLLECTION_THUMBNAIL_TOPIC_ARN,
        Message=json.dumps(message),
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--uuid", "-u", type=str, required=True,
                        help="the uuid of the collection")

    args = parser.parse_args()

    uuid = args.uuid

    invoke(uuid)
