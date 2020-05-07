import argparse
import json
import sys

import boto3

import django

s3 = boto3.resource("s3")

django.setup()

from blob.models import Document  # isort:skip


parser = argparse.ArgumentParser()
parser.add_argument("--sha1sum", "-s",
                    help="the sha1sum of the blob")
parser.add_argument("--uuid", "-u", type=str,
                    help="the uuid of the blob")

args = parser.parse_args()

uuid = args.uuid
sha1sum = args.sha1sum

if not uuid and not sha1sum:
    print("Specify the sha1sum or uuid")
    sys.exit(1)
elif uuid and sha1sum:
    print("You must not specify both the sha1sum and uuid")
    sys.exit(1)
elif uuid:
    kwargs = {"uuid": uuid}
elif sha1sum:
    kwargs = {"sha1sum": sha1sum}

b = Document.objects.get(**kwargs)

obj = s3.Object(bucket_name='bordercore-blobs', key=b.get_s3_key())

print(json.dumps(obj.metadata))
