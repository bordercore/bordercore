import json
import logging
import os
import re
from pathlib import PurePath

import boto3

from lib.elasticsearch_indexer import index_blob as index_blob_es
from requests_aws4auth import AWS4Auth

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, os.environ["AWS_REGION"], "es", session_token=credentials.token)


def handler(event, context):

    try:

        for record in event["Records"]:

            sns_record = json.loads(record["Sns"]["Message"])["Records"][0]
            bucket = sns_record["s3"]["bucket"]["name"]
            log.info(f"bucket: {bucket}")

            # Ignore object delete events
            if sns_record.get("eventName", None) == "ObjectRemoved:Delete":
                continue

            file_changed = sns_record["s3"].get("file_changed", True)

            # If this was triggered by S3, then parse the uuid from the S3 key.
            # Otherwise this must have been called from Django, in which case the
            # uuid was passed in instead.
            try:

                key = sns_record["s3"]["object"]["key"]
                log.info(f"key: {key}")

                # blobs/af351cc4-3b8b-47d5-8048-85e5fb5abe19/cover.jpg
                pattern = re.compile(r"^blobs/(.*?)/")

                matches = pattern.match(key)
                if matches and matches.group(1):
                    uuid = matches.group(1)
                else:
                    # TODO Throw more specific exception
                    raise Exception(f"Can't parse uuid from key: {key}")

                if PurePath(key).name == "cover.jpg" or PurePath(key).name.startswith("cover-"):
                    log.info("Skipping blob")
                    continue

                index_blob_es(uuid=uuid, file_changed=file_changed)

            except KeyError:
                uuid = sns_record["s3"]["uuid"]
                if uuid is None:
                    raise Exception(f"No uuid found in SNS event: {record['Sns']['Message']}")
                print(f"uuid: {uuid}")
                index_blob_es(uuid=uuid, file_changed=file_changed)

        log.info("Lambda finished")

    except Exception as e:
        log.error(f"{type(e)} exception: {e}")
        log.error(sns_record)
        import traceback
        print(traceback.format_exc())
