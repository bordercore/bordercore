import os
import sys

import boto3
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections
import elasticsearch.exceptions
import psycopg2
import psycopg2.extras
import urllib3

import django
from django.conf import settings

from blob.elasticsearch_indexer import index_blob

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'

django.setup()

from blob.models import Document


urllib3.disable_warnings()

BATCH_SIZE = 10
LAST_BLOB_FILE = "/tmp/indexer_es_last_blob.txt"

# Use ssh tunnel to connect to VPC endpoint
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


def get_last_blob():

    try:
        with open(LAST_BLOB_FILE, "r") as file:
            last_blob = file.read().strip()
    except FileNotFoundError:
        return ""
    return last_blob


def blob_exists_in_es(uuid):

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


es = Elasticsearch([settings.ELASTICSEARCH_ENDPOINT], verify_certs=False)

blobs = Document.objects.filter(uuid="09dc76c7-3225-47cc-aa38-f36b072c1d05")

# Text blob
# blobs = Document.objects.filter(uuid="53f90c12-e90d-400f-ab5c-a4ae1bde9b2c")

# Small pdf
# blobs = Document.objects.filter(uuid="a446d1c3-8abd-49a9-a526-1986a78fb517")

# Large pdf
# blobs = Document.objects.filter(uuid="8bc309ba-d275-4f4c-8e3a-7687383df40b")

# All blobs
# blobs = Document.objects.all().order_by("created")

last_blob = get_last_blob()
blob = None

go = False
blob_count = 0
limit = 10000

blobs_to_skip = [
    "ed124f8d-e5c1-4221-bad4-74b64bac152e",
    "9091c1fe-baca-4c5c-a8b8-b059fc75d50a",
    "19109276-21b1-4fb5-a336-87e248afa89d",
    "9c461f7e-7a1b-4f44-a312-053184d803c0",
    "50d894af-8dad-44ab-a15e-2435dd8f827a",
    "56ba664e-e918-4598-b198-8e01da064f75",
    "08406fc2-9d57-4bff-9364-8730a8bb2311",
    "d4cb9434-46d6-411b-8062-1421abbcc624",
    "032adf25-92d7-4f26-914c-83e6e3782281",
    "95546f46-3842-49d4-93d3-82fad914e3ce",
    "0bc6586a-4e8b-4644-b863-374b9fc514fa",
    "b9d3b971-682a-42ba-9db4-6b867edd60eb",
]

blob_batch = []

for blob_info in blobs:

    try:
        if str(blob_info.uuid) in blobs_to_skip:
            continue

        print(f"{blob_count} {blob_info.uuid}")

        if go and blob_exists_in_es(blob_info.uuid):
            continue

        if last_blob != "" and not go:
            if str(blob_info.uuid) == last_blob:
                go = True
            continue
        else:
            blob_count = blob_count + 1
            if blob_count > limit:
                break
            index_blob(uuid=blob_info.uuid)

        print(f"{blob_info.uuid} {blob_info.file_s3} {blob_info.title}")

        with open(LAST_BLOB_FILE, "w") as file:
            file.write(str(blob_info.uuid))

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

# if blob:
#     with open(LAST_BLOB_FILE, "w") as file:
#         file.write(str(blob["uuid"]))
