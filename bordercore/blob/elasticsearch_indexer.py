import base64
import io
import json
import logging
import os
import re
import subprocess
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import PurePath

import boto3
import elasticsearch_dsl
import magic
import requests
from elasticsearch_dsl import DateRange
from elasticsearch_dsl import Document as Document_ES
from elasticsearch_dsl import Integer, Long, Range, Text

try:
    import fitz
except ModuleNotFoundError:
    # Don't worry if this module doesn't exist in production
    pass

from lib.util import get_elasticsearch_connection, is_pdf, is_video

ELASTICSEARCH_INDEX = os.environ.get("ELASTICSEARCH_INDEX", "bordercore")

S3_KEY_PREFIX = "blobs"
S3_BUCKET_NAME = "bordercore-blobs"

DRF_TOKEN = os.environ.get("DRF_TOKEN")

FILE_TYPES_TO_INGEST = [
    "azw3",
    "chm",
    "epub",
    "html",
    "pdf",
    "txt"
]

logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)


def elasticsearch_merge(data, new_data, raise_on_conflict=False):
    """
    This is a monkeypatched version of elasticsearch_dsl.utils.merge()
    which avoids an issue when indexing documents with date_range fields.
    """
    import collections.abc as collections_abc

    from elasticsearch_dsl.utils import AttrDict
    from elasticsearch_dsl.wrappers import Range
    from six import iteritems

    if not (
        isinstance(data, (AttrDict, collections_abc.Mapping))
        and isinstance(new_data, (AttrDict, collections_abc.Mapping))
    ):
        raise ValueError(
            "You can only merge two dicts! Got {!r} and {!r} instead.".format(
                data, new_data
            )
        )

    if isinstance(new_data, Range):
        return

    for key, value in iteritems(new_data):
        if (
            key in data
            and isinstance(data[key], (AttrDict, collections_abc.Mapping))
            and isinstance(value, (AttrDict, collections_abc.Mapping))
            and not isinstance(value, Range)
        ):
            elasticsearch_merge(data[key], value, raise_on_conflict)
        elif key in data and data[key] != value and raise_on_conflict:
            raise ValueError("Incompatible data for key %r, cannot be merged." % key)
        else:
            data[key] = value


class ESBlob(Document_ES):
    uuid = Text()
    bordercore_id = Long()
    sha1sum = Text()
    user_id = Integer()
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
    created_date = Text()
    last_modified = Text()

    class Index:
        name = ELASTICSEARCH_INDEX


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
        raise Exception(f"Error when accessing Bordercore REST API: status code={r.status_code}, prefix={prefix}, param={param}")

    info = r.json()

    # Extract the blob's metadata and store it separately, since it will
    #  be indexed in its own Elasticsearch field
    metadata = {}

    for x in info["metadata"]:
        for key, value in x.items():
            if not key or not value:
                continue
            existing = metadata.get(key.lower(), [])
            existing.append(value)
            metadata[key.lower()] = existing

    # Now that we have a separate copy, remove the blob's metadata from the main object
    info.pop("metadata", None)

    return {
        **info,
        "metadata": metadata
    }


def get_blob_contents_from_s3(blob):

    blob_contents = BytesIO()
    s3_key = f'{S3_KEY_PREFIX}/{blob["uuid"]}/{blob["file"]}'
    s3_client = boto3.client("s3")
    s3_client.download_fileobj(S3_BUCKET_NAME, s3_key, blob_contents)

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

    doc = fitz.open("pdf", io.BytesIO(content))
    return doc.page_count


def delete_metadata(es, uuid):

    q = {
        "query": {
            "term": {
                "uuid": uuid
            }
        },
        "script": {
            "source": "ctx._source.remove(\"metadata\")",
            "lang": "painless"
        }
    }

    es.update_by_query(body=q, index=ELASTICSEARCH_INDEX)


def create_embeddings(uuid):
    lambda_client = boto3.client("lambda")
    lambda_client.invoke(
        FunctionName="CreateEmbeddings",
        InvocationType="Event",
        Payload=json.dumps({"uuid": uuid})
    )


def index_blob(**kwargs):

    es = None
    if kwargs.get("create_connection", True):
        es = get_elasticsearch_connection()

    blob_info = get_blob_info(**kwargs)

    extra_fields = {}
    if "extra_fields" in kwargs:
        extra_fields = kwargs["extra_fields"]

    # An empty string causes a Python datetime validation error,
    #  so convert to "None" to avoid this.
    if blob_info["date"] == "":
        blob_info["date"] = None

    fields = dict(
        uuid=blob_info["uuid"],
        bordercore_id=blob_info["id"],
        sha1sum=blob_info["sha1sum"],
        user_id=blob_info["user"]["id"],
        name=blob_info["name"],
        contents=blob_info["content"],
        doctype=get_doctype(blob_info, blob_info["metadata"]),
        tags=blob_info["tags"],
        filename=str(blob_info["file"]),
        note=blob_info["note"],
        importance=blob_info["importance"],
        date_unixtime=get_unixtime_from_string(blob_info["date"]),
        created_date=blob_info["created"],
        last_modified=blob_info["modified"],
        metadata=blob_info["metadata"],
        **extra_fields
    )

    if blob_info["date"] is not None:
        fields["date"] = get_range_from_date(blob_info["date"])

    article = ESBlob(**fields)
    article.meta.id = blob_info["uuid"]

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
        EFS_DIR = os.environ.get("EFS_DIR", "/tmp/blobs")
        filename = f"{EFS_DIR}/{uuid.uuid4()}-{str(blob_info['file'])}"
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
            except (TypeError, ValueError):
                # A pdf read failure can be caused by many
                #  things. Ignore any such failures.
                pass

        if is_ingestible_file(blob_info["file"]):
            pipeline_args = dict(pipeline="attachment")
            article.data = base64.b64encode(contents).decode("ascii")

        article.save(**pipeline_args)

    else:
        if not kwargs.get("new_blob", True):
            # For existing blobs, remove any existing metadata first before updating,
            #  in case the user is deleting some of it.
            delete_metadata(es, article.uuid)

        # Monkeypatch Elasticsearch DSL to avoid issue with date ranges
        elasticsearch_dsl.utils.merge = elasticsearch_merge

        article.update(doc_as_upsert=True, **fields)

    if "content" in blob_info:
        create_embeddings(blob_info["uuid"])
