import argparse
import json
import pprint

import boto3

import django

django.setup()

from bookmark.models import Bookmark  # isort:skip

client = boto3.client("lambda")


def invoke(uuid):

    bookmark = Bookmark.objects.get(uuid=uuid)

    message = {
        "Records": [
            {
                "eventName": "ObjectCreated: Put",
                "s3": {
                    "bucket": {
                        "name": "bordercore-blobs",
                    },
                    "object": {
                        "key": f"bookmarks/{bookmark.uuid}.png"
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
        FunctionName="CreateBookmarkThumbnail",
        InvocationType="Event",
        LogType="Tail",
        Payload=json.dumps(payload)
    )

    pprint.PrettyPrinter(indent=4).pprint(response)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--uuid", "-u", type=str, required=True,
                        help="the uuid of the bookmark to index")

    args = parser.parse_args()

    uuid = args.uuid

    invoke(uuid)
