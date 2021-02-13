import argparse
import json
import pprint

import boto3

import django

django.setup()


client = boto3.client("lambda")


def invoke(uuid):

    payload = {
        "feed_uuid": uuid
    }

    response = client.invoke(
        ClientContext="MyApp",
        FunctionName="UpdateFeeds",
        InvocationType="Event",
        LogType="Tail",
        Payload=json.dumps(payload)
    )

    pprint.PrettyPrinter(indent=4).pprint(response)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--uuid", "-u", type=str, required=True,
                        help="the feed uuid to update")

    args = parser.parse_args()

    uuid = args.uuid

    invoke(uuid)
