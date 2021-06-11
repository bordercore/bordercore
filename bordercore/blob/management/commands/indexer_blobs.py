import signal
import sys

import elasticsearch.exceptions
import urllib3
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from blob.elasticsearch_indexer import index_blob

from blob.models import Blob  # isort:skip


urllib3.disable_warnings()

es = Elasticsearch(
    [settings.ELASTICSEARCH_ENDPOINT],
    timeout=120,
    verify_certs=False
)


def handler(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, handler)


class Command(BaseCommand):
    help = "Re-index all blobs in Elasticsearch"

    BATCH_SIZE = 10
    LAST_BLOB_FILE = "/tmp/indexer_es_last_blob.txt"

    def add_arguments(self, parser):
        parser.add_argument(
            "--uuid",
            help="The uuid of a single blob to index",
        )
        parser.add_argument(
            "--force",
            help="Force indexing even if the blob exists in Elasticsearch",
            action="store_true"
        )
        parser.add_argument(
            "--limit",
            help="Limit the number of blobs indexed",
            default=100000,
            type=int
        )
        parser.add_argument(
            "--verbose",
            help="Increase output verbosity",
            action="store_true"
        )
        parser.add_argument(
            "--create-connection",
            help="Create connection to Elasticsearch",
            default=False,
            action="store_true"
        )

    @atomic
    def handle(self, *args, uuid, force, create_connection, limit, verbose, **kwargs):

        last_blob = None

        if uuid:
            # A single blob
            blobs = Blob.objects.filter(uuid=uuid)
        else:
            # All blobs
            blobs = Blob.objects.filter(is_indexed=True).order_by("created")
            last_blob = self.get_last_blob()

            # Use this to only include "ingestible" file types
            # blobs = Blob.objects.exclude(is_indexed=False).filter(file__iregex=r".(azw3|chm|epub|html|pdf|txt)$").order_by("created")

        blob = None

        go = True if uuid else False

        blob_count = 0

        self.blob_batch = []

        for blob_info in blobs:

            try:

                if verbose:
                    self.stdout.write(f"{blob_count} {blob_info.uuid}")

                if go and not force and self.blob_exists_in_es(blob_info.uuid):
                    if verbose:
                        self.stdout.write(f"{blob_info.uuid} Blob already indexed. Not re-indexing")
                    continue

                if last_blob != "" and not go:
                    if str(blob_info.uuid) == last_blob:
                        go = True
                    continue
                else:
                    blob_count = blob_count + 1
                    if blob_count > limit:
                        break
                    index_blob(uuid=blob_info.uuid, create_connection=create_connection)

                self.stdout.write(f"{blob_info.uuid} {blob_info.file} {blob_info.name}")

                self.write_checkpoint(blob_info.uuid)

            except elasticsearch.exceptions.TransportError as e:
                self.stdout.write(f"{blob_info.uuid} Elasticsearch Error: {e}")
                import traceback
                self.stdout.write(traceback.format_exc())
                sys.exit(1)
            except Exception as e:
                self.stdout.write(f"Type of error: {type(e)}")
                self.stdout.write(f"{blob_info.uuid} Exception: {e}")
                import traceback
                self.stdout.write(traceback.format_exc())
                sys.exit(1)

        if blob:
            self.write_checkpoint(str(blob["uuid"]))

    def write_checkpoint(self, uuid):
        with open(self.LAST_BLOB_FILE, "w") as file:
            file.write(str(uuid))

    def get_last_blob(self):

        try:
            with open(self.LAST_BLOB_FILE, "r") as file:
                last_blob = file.read().strip()
            self.stdout.write(f"Reading checkpoint from {self.LAST_BLOB_FILE} to resume where we left off...")
        except FileNotFoundError:
            return ""
        return last_blob

    def blob_exists_in_es(self, uuid):

        search_object = {"query": {"term": {"uuid": uuid}}, "_source": ["uuid"]}
        results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        return int(results["hits"]["total"]["value"])

    def add_to_batch(self, blob, ingestible=False):

        self.blob_batch.append(blob)
        if len(self.blob_batch) == self.BATCH_SIZE:
            if ingestible:
                # bulk(connections.get_connection(), (d.to_dict(True) for d in blob_batch), max_chunk_bytes=1268032, chunk_size=1, pipeline="attachment")
                bulk(connections.get_connection(), (d.to_dict(True) for d in self.blob_batch), max_chunk_bytes=1268032, pipeline="attachment")
            else:
                bulk(connections.get_connection(), (d.to_dict(True) for d in self.blob_batch))
            self.blob_batch = []
