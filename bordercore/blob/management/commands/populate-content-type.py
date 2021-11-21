# Update a blob's content type field in Elasticsearch

import base64
import json
import sys

import boto3

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from blob.models import Blob
from lib.util import get_elasticsearch_connection

client = boto3.client("lambda")

function_name = "IndexBlob"

es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)


class Command(BaseCommand):
    help = "Update a blob's content type field in Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            help="The maximum number of blobs to process",
            default=10000
        )

    @atomic
    def handle(self, *args, limit, **kwargs):

        count = 0

        found = self.get_blobs_to_update()
        self.stdout.write(f"Total: {found['total']['value']}")

        for hit in found["hits"]:
            self.stdout.write(f"Re-indexing {hit['_source']['uuid']} {hit['_source']['filename']}")

            blob = Blob.objects.get(uuid=hit["_source"]["uuid"])

            count = count + 1

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
                                    "key": blob.s3_key
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

                self.stdout.write(response)

                if response["StatusCode"] != 200:
                    self.stdoute.write(response)

            except Exception as e:
                self.stderror.write(f"Exception during invoke_lambda: {e}")

            if count == limit:
                sys.exit(0)

    def get_blobs_to_update(self):
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

        return es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]
