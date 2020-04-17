import argparse
import os
import signal
import sys

import boto3
import psycopg2
import psycopg2.extras
import urllib3

import django
import elasticsearch.exceptions
from blob.elasticsearch_indexer import index_blob
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections

django.setup()

from blob.models import Document, BLOBS_NOT_TO_INDEX  # isort:skip


urllib3.disable_warnings()

BATCH_SIZE = 10
LAST_BLOB_FILE = "/tmp/indexer_es_last_blob.txt"

# Use ssh tunnel to connect to Elasticsearch endpoint
s3_bucket_name = "bordercore-blobs"
s3_key_prefix = "blobs"

connections.create_connection(
    hosts=[settings.ELASTICSEARCH_ENDPOINT],
    timeout=1200,
    verify_certs=False
)

s3client = boto3.client("s3")

db_endpoint = "bordercore.cvkm90zuldto.us-east-1.rds.amazonaws.com"
db_username = "bordercore"
db_password = os.environ.get("DATABASE_PASSWORD")
db_database = "bordercore"

db_conn = psycopg2.connect("dbname=%s port=5432 host=%s user=%s password=%s" % (db_database, db_endpoint, db_username, db_password))

debug_count = 0


def handler(signum, frame):
    print(f"Count: {debug_count}")
    sys.exit(0)


signal.signal(signal.SIGINT, handler)


def write_checkpoint(uuid):
    with open(LAST_BLOB_FILE, "w") as file:
        file.write(str(uuid))


def get_last_blob():

    try:
        with open(LAST_BLOB_FILE, "r") as file:
            last_blob = file.read().strip()
        print(f"Using {LAST_BLOB_FILE} to resume where we left off...")
    except FileNotFoundError:
        return ""
    return last_blob


def blob_exists_in_es(uuid):

    global debug_count
    debug_count += 1
    search_object = {"query": {"term": {"uuid.keyword": uuid}}, "_source": ["uuid"]}
    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
    return int(results["hits"]["total"]["value"])


def add_to_batch(blob, ingestible=False):

    blob_batch.append(blob)
    if len(blob_batch) == BATCH_SIZE:
        if ingestible:
            # bulk(connections.get_connection(), (d.to_dict(True) for d in blob_batch), max_chunk_bytes=1268032, chunk_size=1, pipeline="attachment")
            bulk(connections.get_connection(), (d.to_dict(True) for d in blob_batch), max_chunk_bytes=1268032, pipeline="attachment")
        else:
            bulk(connections.get_connection(), (d.to_dict(True) for d in blob_batch))
        blob_batch = []


parser = argparse.ArgumentParser()
parser.add_argument("--force", "-f",
                    help="force indexing even if the blob exists",
                    action="store_true")
parser.add_argument("--limit", "-l", default=100000, type=int,
                    help="limit the number of blobs indexed")
parser.add_argument("--verbose", "-v",
                    help="increase output verbosity",
                    action="store_true")
parser.add_argument("--uuid", "-u", type=str,
                    help="the uuid of a single blob to index")

args = parser.parse_args()

force_index = args.force
limit = args.limit
verbose = args.verbose
uuid = args.uuid

es = Elasticsearch([settings.ELASTICSEARCH_ENDPOINT], verify_certs=False)

if uuid:
    # A single blob
    blobs = Document.objects.filter(uuid=uuid)
else:
    # All blobs
    blobs = Document.objects.exclude(uuid__in=BLOBS_NOT_TO_INDEX).order_by("created")

    # Use this to only include "ingestible" file types
    # blobs = Document.objects.exclude(uuid__in=BLOBS_NOT_TO_INDEX).filter(file__iregex=r".(azw3|chm|epub|html|pdf|txt)$").order_by("created")

last_blob = get_last_blob()
blob = None

go = True if uuid else False

blob_count = 0

blob_batch = []

for blob_info in blobs:

    try:

        if verbose:
            print(f"{blob_count} {blob_info.uuid}")

        if go and blob_exists_in_es(blob_info.uuid) and not force_index:
            if verbose:
                print(f"{blob_info.uuid} Blob already indexed. Not re-indexing")
            continue

        if last_blob != "" and not go:
            if str(blob_info.uuid) == last_blob:
                go = True
            continue
        else:
            blob_count = blob_count + 1
            if blob_count > limit:
                break
            index_blob(uuid=blob_info.uuid, create_connection=False)

        print(f"{blob_info.uuid} {blob_info.file} {blob_info.title}")

        write_checkpoint(blob_info.uuid)

    except elasticsearch.exceptions.TransportError as e:
        print(f"{blob_info.uuid} Elasticsearch Error: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        print(f"Type of error: {type(e)}")
        print(f"{blob_info.uuid} Exception: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
    # except elasticsearch.exceptions.ConnectionError as e:
    #     print(e)
    #     sys.exit(1)

db_conn.commit()
db_conn.close()

if blob:
    write_checkpoint(str(blob["uuid"]))
