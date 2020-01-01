import base64
from datetime import datetime
from io import BytesIO
import os
import re

import boto3
from elasticsearch import RequestsHttpConnection
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Boolean, Document as Document_ES, DateRange, Integer, Long, Range, Text
from elasticsearch_dsl.connections import connections
import magic
import psycopg2
import psycopg2.extras


ES_ENDPOINT = os.environ.get("ELASTICSEARCH_ENDPOINT", "localhost")
ES_PORT = 9200
ES_INDEX_NAME = "bordercore"

DB_ENDPOINT = "bordercore.cvkm90zuldto.us-east-1.rds.amazonaws.com"
DB_USERNAME = "bordercore"
DB_PASSWORD = os.environ.get("DATABASE_PASSWORD")
DB_DATABASE = "bordercore"

S3_KEY_PREFIX = "blobs"
S3_BUCKET_NAME = "bordercore-blobs"

FILE_TYPES_TO_INGEST = [
    'azw3',
    'chm',
    'epub',
    'html',
    'pdf',
    'txt'
]

s3client = boto3.client("s3")
db_conn = psycopg2.connect("dbname=%s port=5432 host=%s user=%s password=%s" % (DB_DATABASE, DB_ENDPOINT, DB_USERNAME, DB_PASSWORD))


class ESBlob(Document_ES):
    uuid = Text()
    bordercore_id = Long()
    sha1sum = Text()
    user_id = Integer()
    is_private = Boolean()
    date = DateRange()
    title = Text()
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
    elif metadata.get("is_book", ""):
        return "book"
    elif blob["sha1sum"] is not None:
        return "blob"
    else:
        return "document"


def is_ingestible_file(filename):

    _, file_extension = os.path.splitext(filename)
    if file_extension[1:].lower() in FILE_TYPES_TO_INGEST:
        return True
    else:
        return False


def get_blob_info(**kwargs):

    param = None
    if kwargs.get("sha1sum", None):
        predicate = "WHERE bd.sha1sum = %s"
        param = kwargs["sha1sum"]
    elif kwargs.get("uuid", None):
        predicate = "WHERE bd.uuid = %s"
        param = kwargs["uuid"]
    else:
        raise Exception("Must pass in uuid or sha1sum")

    sql = f"SELECT * FROM blob_document bd {predicate}"

    cursor = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(sql, (param,))
    results = cursor.fetchone()

    sql = f"""
    SELECT tt.name FROM blob_document bd
    JOIN blob_document_tags bdt ON (bd.id = bdt.document_id)
    JOIN tag_tag tt ON (bdt.tag_id = tt.id)
    {predicate}
    """

    cursor = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(sql, (param,))

    dict2 = {key: value for key, value in results.items()}
    dict2["tags"] = [x[0] for x in cursor.fetchall()]

    return dict2


def get_blob_metadata(uuid):

    sql = """
    SELECT bd.uuid,bm.name,bm.value FROM blob_document bd
    JOIN blob_metadata bm ON (bd.id = bm.blob_id)
    WHERE bd.uuid=%s
    """

    cursor = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(sql, (uuid,))

    metadata = {}

    for row in cursor.fetchall():

        # Empty field names will cause an Elasticsearch error
        if row["name"] == "":
            continue
        existing = metadata.get(row["name"].lower(), [])
        existing.append(row["value"])
        metadata[row["name"].lower()] = existing

    return metadata


def get_blob_contents_from_s3(blob):

    blob_contents = BytesIO()
    s3_key = f'{S3_KEY_PREFIX}/{blob["sha1sum"][:2]}/{blob["sha1sum"]}/{blob["file"]}'
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


def index_blob(**kwargs):

    connections.create_connection(
        hosts=[{"host": ES_ENDPOINT, "port": ES_PORT}],
        use_ssl=False,
        timeout=1200,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    blob_info = get_blob_info(**kwargs)
    metadata = get_blob_metadata(blob_info["uuid"])

    # An empty string causes a Python datetime validation error,
    #  so convert to "None" to avoid this.
    if blob_info["date"] == "":
        blob_info["date"] = None

    article = ESBlob(
        meta={"id": blob_info["uuid"]},
        uuid=blob_info["uuid"],
        bordercore_id=blob_info["id"],
        sha1sum=blob_info["sha1sum"],
        user_id=blob_info["user_id"],
        is_private=blob_info["is_private"],
        title=blob_info["title"],
        contents=blob_info["content"],
        doctype=get_doctype(blob_info, metadata),
        tags=blob_info["tags"],
        filename=str(blob_info["file"]),
        note=blob_info["note"],
        importance=blob_info["importance"],
        date_unixtime=get_unixtime_from_string(blob_info["date"]),
        last_modified=blob_info["modified"],
        **metadata
    )

    if blob_info["date"] is not None:
        article.date = get_range_from_date(blob_info["date"])

    pipeline_args = {}

    if blob_info["sha1sum"]:

        # Even if this is not an ingestible file, we need to download the blob
        #  in order to determine the content type
        contents = get_blob_contents_from_s3(blob_info)
        article.content_type = magic.from_buffer(contents, mime=True)

        if is_ingestible_file(blob_info["file"]):
            article.data = base64.b64encode(contents).decode("ascii")
            pipeline_args = dict(max_chunk_bytes=1268032, chunk_size=1, pipeline="attachment")

    bulk(connections.get_connection(), (d.to_dict(True) for d in [article]), pipeline_args)

    # Rollback to avoid idle transactions
    db_conn.rollback()
