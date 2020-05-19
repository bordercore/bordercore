# Re-index all blobs without a "content-type" field

import base64
import json

import boto3
import urllib3
from elasticsearch import Elasticsearch

import django
from django.conf import settings

urllib3.disable_warnings()

django.setup()

from blob.models import Blob  # isort:skip


client = boto3.client("lambda")

function_name = "IndexBlob"

es = Elasticsearch(
    [settings.ELASTICSEARCH_ENDPOINT],
    timeout=120,
    verify_certs=False
)

# Look for all documents without a "content type" field

search_object = {
    "query": {
        "function_score": {
            "random_score": {
            },
            "query": {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "must_not": [
                                    {
                                        "exists": {
                                            "field": "content_type"
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "term": {
                                "doctype": "blob"
                            }
                        }
                    ]
                }
            }
        }
    },
    "from": 0, "size": 1000,
    "_source": ["content_type", "doctype", "filename", "sha1sum", "title", "uuid"]
}

found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]

print(f"Total: {found['total']['value']}")

for hit in found["hits"]:
    print(f"Re-indexing {hit['_source']['uuid']} {hit['_source']['filename']}")

    blob = Blob.objects.get(uuid=hit["_source"]["uuid"])
    try:

        event = {
            "Records":
            [
                {
                    "s3": {
                        "bucket": {
                            "name": "bordercore-blobs"
                        },
                        "object": {
                            "key": blob.get_s3_key()
                        }
                    }
                }
            ]
        }

        wrapper = {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps(event)
                    }
                }
            ]
        }

        response = client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            LogType="None",
            ClientContext=base64.b64encode(json.dumps({}).encode()).decode(),
            Payload=json.dumps(wrapper).encode()
        )

        print(response)

        if response["StatusCode"] != 200:
            print(response)

    except Exception as e:
        print(f"Exception during invoke_lambda: {e}")
