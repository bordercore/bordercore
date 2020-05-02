import argparse
import json
import pprint

import boto3

import django

django.setup()

from blob.models import Document  # isort:skip

client = boto3.client("lambda")


def invoke(uuid):

    blob = Document.objects.get(uuid=uuid)

    message = {
        "Records": [
            {
                "eventName": "ObjectCreated: Put",
                "s3": {
                    "bucket": {
                        "name": "bordercore-blobs",
                    },
                    "object": {
                        "key": f"blobs/{blob.sha1sum[:2]}/{blob.sha1sum}/{blob.file}"
                    }
                }
            }
        ]
    }

    payload = {
        "Records": [
            {
                "Sns": {
                    "Message": json.dumps(message)
                }
            }
        ]
    }

    response = client.invoke(
        ClientContext="MyApp",
        FunctionName="CreateThumbnail",
        InvocationType="Event",
        LogType="Tail",
        Payload=json.dumps(payload)
    )

    pprint.PrettyPrinter(indent=4).pprint(response)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--uuid", "-u", type=str, required=True,
                        help="the uuid of the blob to index")

    args = parser.parse_args()

    uuid = args.uuid

    invoke(uuid)
