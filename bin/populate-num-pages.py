# Scan every pdf on the file system, count the number of pages,
#  then update the Elasticsearch index.

import io
import re
import sys
from pathlib import Path

from elasticsearch import Elasticsearch
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

import django

from lib.util import is_pdf

django.setup()

from blob.models import Blob  # isort:skip


BLOB_DIR = "/home/media"

index_name = "bordercore"
endpoint = "http://localhost:9200"

es = Elasticsearch([endpoint], verify_certs=False)


def update_metadata(uuid, num_pages):

    request_body = {
        "query": {
            "term": {
                "uuid.keyword": uuid
            }
        },
        "script": {
            "source": f"ctx._source.num_pages={num_pages}",
            "lang": "painless"
        }
    }

    return es.update_by_query(index=index_name, body=request_body)


limit = 10000
count = 0
go = False

for x in Path(f"{BLOB_DIR}/blobs").rglob("*"):
    if x.is_file():
        print(x)
        m = re.search(r"^/home/media/blobs/\w{2}/(\w{40})/(.+)", str(x))
        if m:
            count = count + 1
            sha1sum = m.group(1)

            if sha1sum == "d5d538233774073e8310bd991ca83cbee4900f80":
                go = True

            if not go:
                continue

            filename = m.group(2)
            print(sha1sum)

            if not is_pdf(filename):
                continue
            blob = Blob.objects.get(sha1sum=sha1sum)
            with open(x, 'rb') as content_file:
                content = content_file.read()

            f = io.BytesIO(content)

            try:
                input_pdf = PdfFileReader(f)
            except (TypeError, PdfReadError):
                continue

            try:
                num_pages = input_pdf.getNumPages()
            except (ValueError, PdfReadError):
                continue

            result = update_metadata(blob.uuid, num_pages)
            print(f" {blob.uuid} update num_pages to {num_pages}: {result}")

            count = count + 1
            if count == limit:
                sys.exit(0)
