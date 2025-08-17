import argparse
import json
import re
import time

import boto3

import django
from django.conf import settings

django.setup()

from bookmark.models import Bookmark  # isort:skip

client = boto3.client("lambda")

DELAY = 5


def populate_action(dry_run):

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    s3_resource = boto3.resource("s3")
    unique_uuids = set()

    paginator = s3_resource.meta.client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^bookmarks/(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)", str(key["Key"]))
            if m:
                # print(m.group(1))
                unique_uuids.add(m.group(1))

    to_process = [x for x in Bookmark.objects.all() if str(x.uuid) not in unique_uuids]
    print(f"Processing {len(to_process)} bookmarks")

    for bookmark in to_process:
        print(f"{bookmark.uuid} {bookmark.created} {bookmark.name}")
        if not dry_run:
            invoke(bookmark.uuid, dry_run)
            time.sleep(DELAY)


def invoke(uuid, dry_run):

    bookmark = Bookmark.objects.get(uuid=uuid)

    SNS_TOPIC = settings.SNS_TOPIC_ARN
    client = boto3.client("sns")

    message = {
        "url": bookmark.url,
        "s3key": f"bookmarks/{bookmark.uuid}.png",
        "puppeteer": {
            "screenshot": {
                "type": "jpeg",
                "quality": 50,
                "omitBackground": False
            }
        }
    }

    client.publish(
        TopicArn=SNS_TOPIC,
        Message=json.dumps(message),
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--uuid", "-u", type=str,
                       help="the uuid of the bookmark to index")
    group.add_argument("--all", "-a", action="store_true",
                       help="create thumbnails for all bookmarks that need them")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Dry run. Take no action")

    args = parser.parse_args()

    uuid = args.uuid
    all = args.all
    dry_run = args.dry_run

    if uuid:
        invoke(uuid, dry_run)
    elif all:
        populate_action(dry_run)
