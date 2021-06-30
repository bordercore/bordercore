import base64
import io
import logging
import os
import re
import subprocess
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import PurePath

import boto3
import magic
import requests
from elasticsearch import RequestsHttpConnection
from elasticsearch_dsl import Boolean, DateRange
from elasticsearch_dsl import Document as Document_ES
from elasticsearch_dsl import Integer, Long, Range, Text
from elasticsearch_dsl.connections import connections
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

from lib.util import is_pdf, is_video

ES_ENDPOINT = os.environ.get("ELASTICSEARCH_ENDPOINT", "localhost")
ES_PORT = 9200
ES_INDEX_NAME = "bordercore"

S3_KEY_PREFIX = "blobs"
S3_BUCKET_NAME = "bordercore-blobs"

EFS_DIR = os.environ.get("EFS_DIR", "/tmp")
BLOBS_DIR = f"{EFS_DIR}/blobs"

DRF_TOKEN = os.environ.get("DRF_TOKEN")

FILE_TYPES_TO_INGEST = [
    'azw3',
    'chm',
    'epub',
    'html',
    'pdf',
    'txt'
]

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)

s3client = boto3.client("s3")


class ESBlob(Document_ES):
    uuid = Text()
    bordercore_id = Long()
    sha1sum = Text()
    user_id = Integer()
    is_private = Boolean()
    date = DateRange()
    name = Text()
    contents = Text()
    doctype = Text()
    tags = Text()
    filename = Text()
    note = Text()
    url = Text()
    importance = Integer()
    date_unixtime = Long()
    last_modified = Text()

    class Index:
        name = ES_INDEX_NAME


def get_doctype(blob, metadata):
    if blob["is_note"] is True:
        return "note"
    elif "is_book" in metadata:
        return "book"
    elif blob["sha1sum"] is not None:
        return "blob"
    else:
        return "document"


def is_ingestible_file(filename):

    file_extension = PurePath(str(filename)).suffix
    if file_extension[1:].lower() in FILE_TYPES_TO_INGEST:
        return True
    else:
        return False


def get_blob_info(**kwargs):

    if "sha1sum" in kwargs:
        prefix = "sha1sums"
        param = kwargs["sha1sum"]
    elif "uuid" in kwargs:
        prefix = "blobs"
        param = kwargs["uuid"]
    else:
        raise ValueError("Must pass in uuid or sha1sum")

    headers = {"Authorization": f"Token {DRF_TOKEN}"}

    session = requests.Session()

    # Ignore .netrc files. Useful for local debugging.
    session.trust_env = False

    r = session.get(f"https://www.bordercore.com/api/{prefix}/{param}/", headers=headers)

    if r.status_code != 200:
        raise Exception(f"Error when accessing Bordercore REST API: status code={r.status_code}")

    info = r.json()

    metadata = {}

    for x in info["metadata_set"]:
        for key, value in x.items():
            existing = metadata.get(key.lower(), [])
            existing.append(value)
            metadata[key.lower()] = existing

    return {
        **info,
        "metadata": metadata
    }


def get_blob_contents_from_s3(blob):

    blob_contents = BytesIO()
    s3_key = f'{S3_KEY_PREFIX}/{blob["uuid"]}/{blob["file"]}'
    s3client.download_fileobj(S3_BUCKET_NAME, s3_key, blob_contents)

    blob_contents.seek(0)
    return blob_contents.read()


def get_unixtime_from_string(date):

    if date is None or date == "":
        return None

    return_date = None

    if re.search(r"^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d$", date):
        return_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%s")
    elif re.search(r"^\d\d\d\d-\d\d-\d\d$", date):
        return_date = datetime.strptime(date, "%Y-%m-%d").strftime("%s")
    elif re.search(r"^\d\d\d\d-\d\d$", date):
        return_date = datetime.strptime(f"{date}-01", "%Y-%m-%d").strftime("%s")
    elif re.search(r"^\d\d\d\d$", date):
        return_date = datetime.strptime(f"{date}-01-01", "%Y-%m-%d").strftime("%s")
    else:

        m = re.search(r"^\[(\d\d\d\d-\d\d) TO \d\d\d\d-\d\d\]$", date)
        if m:
            year_month = m.group(1)
            return_date = datetime.strptime(f"{year_month}-01", "%Y-%m-%d").strftime("%s")
        else:
            raise ValueError(f"Date format not recognized: {date}")

    return return_date


def get_range_from_date(date):

    m = re.search(r"^\[(\d\d\d\d-\d\d) TO (\d\d\d\d-\d\d)\]$", date)
    if m:
        range = Range(gte=m.group(1), lte=m.group(2))
    else:
        range = Range(gte=date, lte=date)

    return range


def get_duration(filename):

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename
        ],
        capture_output=True
    )

    return float(result.stdout)


def get_num_pages(content):

    input_pdf = PdfFileReader(io.BytesIO(content), strict=False)

    return input_pdf.getNumPages()


def index_blob(**kwargs):

    if kwargs.get("create_connection", True):
        connections.create_connection(
            hosts=[{"host": ES_ENDPOINT, "port": ES_PORT}],
            use_ssl=False,
            timeout=1200,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

    blob_info = get_blob_info(**kwargs)

    # An empty string causes a Python datetime validation error,
    #  so convert to "None" to avoid this.
    if blob_info["date"] == "":
        blob_info["date"] = None

    fields = dict(
        uuid=blob_info["uuid"],
        bordercore_id=blob_info["id"],
        sha1sum=blob_info["sha1sum"],
        user_id=blob_info["user"],
        is_private=blob_info["is_private"],
        name=blob_info["name"],
        contents=blob_info["content"],
        doctype=get_doctype(blob_info, blob_info["metadata"]),
        tags=blob_info["tags"],
        filename=str(blob_info["file"]),
        note=blob_info["note"],
        importance=blob_info["importance"],
        date_unixtime=get_unixtime_from_string(blob_info["date"]),
        last_modified=blob_info["modified"],
        **blob_info["metadata"]
    )

    article = ESBlob(**fields)
    article.meta.id = blob_info["uuid"]

    if blob_info["date"] is not None:
        article.date = get_range_from_date(blob_info["date"])

    pipeline_args = {}

    # If only the metadata has changed and not the file itself,
    #  don't bother re-indexing the file. Upsert the metadata.
    file_changed = kwargs.get("file_changed", True)
    log.info(f"file_changed: {file_changed}")

    if blob_info["sha1sum"] and file_changed:

        log.info("ingesting the blob")
        # Even if this is not an ingestible file, we need to download the blob
        #  in order to determine the content type
        contents = get_blob_contents_from_s3(blob_info)

        article.size = len(contents)
        log.info(f"Size: {article.size}")

        # Dump the blob contents to a file. We do this rather than process in
        #  memory because some large blobs are too big to handle this way.
        filename = f"{BLOBS_DIR}/{uuid.uuid4()}-{str(blob_info['file'])}"
        with open(filename, "wb") as file:
            newFileByteArray = bytearray(contents)
            file.write(newFileByteArray)

        article.content_type = magic.from_file(filename, mime=True)

        if is_video(blob_info["file"]):
            try:
                article.duration = get_duration(filename)
                log.info(f"Video duration: {article.duration}")
            except Exception as e:
                log.error(f"Exception determing video duration: {e}")

        os.remove(filename)

        if is_pdf(blob_info["file"]):
            try:
                article.num_pages = get_num_pages(contents)
                log.info(f"Number of pages: {article.num_pages}")
            except (PdfReadError, TypeError, ValueError):
                # A pdf read failure can be caused by many
                #  things. Ignore any such failures.
                pass

        if is_ingestible_file(blob_info["file"]):
            pipeline_args = dict(pipeline="attachment")
            article.data = base64.b64encode(contents).decode("ascii")

        article.save(**pipeline_args)

    else:
        article.update(doc_as_upsert=True, **fields)
