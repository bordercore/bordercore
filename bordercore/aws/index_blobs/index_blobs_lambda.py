import json
import logging
import os
import re
from os.path import basename

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

            file_changed = sns_record["s3"]["file_changed"]

            # If this was triggered by S3, then parse the sha1sum from the S3 key.
            # Otherwise this must have been called from Django, in which case the
            # uuid was passed in instead.
            try:

                key = sns_record["s3"]["object"]["key"]
                log.info(f"key: {key}")

                # blobs/d9/d941cfc33c4b40a8c3e576a33343b7adfb7bac69/
                pattern = re.compile(f"^blobs/\w\w/([0-9a-f]{{40}})/")

                matches = pattern.match(key)
                if matches and matches.group(1):
                    sha1sum = matches.group(1)
                else:
                    # TODO Throw more specific exception
                    raise Exception(f"Can't parse sha1sum from key: {key}")

                if basename(key) == "cover.jpg" or basename(key).startswith("cover-"):
                    log.info(f"Skipping blob")
                    continue

                index_blob_es(sha1sum=sha1sum, file_changed=file_changed)

            except KeyError:
                uuid = sns_record["s3"]["uuid"]
                if uuid is None:
                    raise Exception(f"No uuid found in SNS event: {record['Sns']['Message']}")
                print(f"uuid: {uuid}")
                index_blob_es(uuid=uuid, file_changed=file_changed)

        log.info("Lambda finished")

    except Exception as e:
        log.error(f"{type(e)} exception: {e}")
        import traceback
        print(traceback.format_exc())
