import argparse
import json
import sys

import boto3

import django

django.setup()


client = boto3.client("lambda")


def invoke(uuid, text):

    args = {
        "FunctionName": "CreateEmbeddings",
        "LogType": "Tail",
    }

    if uuid:
        payload = {
            "uuid": uuid
        }
        args["InvocationType"] = "Event"
    else:
        payload = {
            "text": text
        }
        args["InvocationType"] = "RequestResponse"

    args["Payload"] = json.dumps(payload)

    response = client.invoke(**args)

    print(response["Payload"].read())


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--uuid", "-u", type=str,
                        help="the uuid of the blob")
    parser.add_argument("--text", "-t", type=str,
                        help="the text to create embeddings")

    args = parser.parse_args()

    uuid = args.uuid
    text = args.text

    if not uuid and not text:
        print("Please provide either a uuid or text")
        sys.exit(1)

    invoke(uuid, text)
