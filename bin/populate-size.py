# Scan every blob on the file system, calculate its size,
#  then update the Elasticsearch index.

import re
import sys
from pathlib import Path

from elasticsearch import Elasticsearch

import django

django.setup()

from blob.models import Document  # isort:skip


BLOB_DIR = "/home/media"

index_name = "bordercore"
endpoint = "http://localhost:9200"

es = Elasticsearch([endpoint], verify_certs=False)


def has_size_field(sha1sum):

    body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": 1
                        }
                    },
                    {
                        "term": {
                            "sha1sum.keyword": sha1sum
                        }
                    },
                    {
                        "bool": {
                            "must": [
                                {
                                    "exists": {
                                        "field": "size"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 1,
        "_source": ["title",
                    "uuid"]
    }

    results = es.search(index=index_name, body=body)
    return(results["hits"]["hits"])


def update_metadata(uuid, size):

    request_body = {
        "query": {
            "term": {
                "uuid.keyword": uuid
            }
        },
        "script": {
            "source": f"ctx._source.size={size}",
            "lang": "painless"
        }
    }

    return es.update_by_query(index=index_name, body=request_body)


limit = 10000
count = 0
go = False

for x in Path(f"{BLOB_DIR}/blobs").rglob("*"):
    if x.is_file():
        m = re.search(r"^/home/media/blobs/\w{2}/(\w{40})/(.+)", str(x))
        if m:
            count = count + 1
            sha1sum = m.group(1)

            if sha1sum == "8f73de65a0902d836df4bf5f11fd080d583e2d3e":
                go = True

            if not go:
                continue

            filename = m.group(2)

            if filename in ["cover.jpg", "cover-small.jpg", "cover-large.jpg"]:
                continue

            print(f"{sha1sum} {x}")

            if has_size_field(sha1sum):
                continue

            blob = Document.objects.get(sha1sum=sha1sum)
            with open(x, 'rb') as content_file:
                content = content_file.read()

            size = len(content)

            result = update_metadata(blob.uuid, size)
            print(f" {blob.uuid} update size to {size}: {result}")

            count = count + 1
            if count == limit:
                sys.exit(0)
