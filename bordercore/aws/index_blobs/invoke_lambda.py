import argparse
import json
import pprint

import boto3

import django

django.setup()

from blob.models import Blob  # isort:skip

client = boto3.client("lambda")


def invoke(uuid, file_changed):

    blob = Blob.objects.get(uuid=uuid)

    message = {
        "Records": [
            {
                "eventName": "ObjectCreated: Put",
                "s3": {
                    "bucket": {
                        "name": "bordercore-blobs",
                    },
                    "file_changed": file_changed,
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
        FunctionName="IndexBlob",
        InvocationType="Event",
        LogType="Tail",
        Payload=json.dumps(payload)
    )

    pprint.PrettyPrinter(indent=4).pprint(response)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--file_changed", "-f", default=False,
                        help="force re-indexing of the contents of the blob",
                        action="store_true")
    parser.add_argument("--uuid", "-u", type=str, required=True,
                        help="the uuid of the blob to index")

    args = parser.parse_args()

    file_changed = args.file_changed
    uuid = args.uuid

    invoke(uuid, file_changed)
