import re

import boto3
import pytest

import django
from django.conf import settings
from django.db.models import Q

from lib.util import get_elasticsearch_connection, get_missing_bookmark_ids

pytestmark = pytest.mark.data_quality

django.setup()

from bookmark.models import Bookmark  # isort:skip


bucket_name = settings.AWS_STORAGE_BUCKET_NAME


@pytest.fixture()
def es():

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)
    yield es


def test_bookmarks_in_db_exist_in_elasticsearch(es):
    "Assert that all bookmarks in the database also exist in Elasticsearch"
    bookmarks = Bookmark.objects.all().only("uuid")

    step = 50
    for batch in range(0, len(bookmarks), step):
        batch_size = len(bookmarks[batch:batch + step])

        query = [
            {
                "term": {
                    "uuid": str(b.uuid)
                }
            }
            for b
            in bookmarks[batch:batch + step]
        ]

        search_object = {
            "query": {
                "bool": {
                    "should": query
                }
            },
            "size": batch_size,
            "_source": ["uuid"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        if found["hits"]["total"]["value"] != batch_size:
            missing_uuids = get_missing_bookmark_ids(bookmarks[batch:batch + step], found)
            uuid_list = "\nuuid:".join(x for x in missing_uuids)
            assert False, f"bookmarks found in the database but not in Elasticsearch, \nuuid:{uuid_list}"


def test_bookmark_tags_match_elasticsearch(es):
    "Assert that all bookmarks tags match those found in Elasticsearch"
    bookmarks = Bookmark.objects.filter(tags__isnull=False).only("uuid", "tags").order_by("uuid").distinct("uuid")

    step = 50
    for batch in range(0, len(bookmarks), step):
        batch_size = len(bookmarks[batch:batch + step])

        query = [
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "uuid": b.uuid
                            }
                        },
                        {
                            "bool": {
                                "must": [
                                    {
                                        "term": {
                                            "tags.keyword": tag.name
                                        }
                                    }
                                    for tag in b.tags.all()
                                ]
                            }
                        }
                    ]
                }
            }
            for b
            in bookmarks[batch:batch + step]
        ]

        search_object = {
            "query": {
                "bool": {
                    "should": query
                }
            },
            "size": batch_size,
            "_source": ["uuid"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        assert found["hits"]["total"]["value"] == batch_size, \
            "bookmark's tags don't match those found in Elasticsearch: " + get_missing_bookmark_ids(bookmarks[batch:batch + step], found)


def test_elasticsearch_bookmarks_exist_in_db(es):
    "Assert that all bookmarks in Elasticsearch exist in the database"

    search_object = {
        "query": {
            "term": {
                "doctype": "bookmark"
            }
        },
        "from": 0, "size": 10000,
        "_source": ["uuid"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    missing_uuids = []
    for bookmark in found:
        if Bookmark.objects.filter(uuid=bookmark["_source"]["uuid"]).count() != 1:
            missing_uuids.append(bookmark["_source"]["uuid"])
    if missing_uuids:
        uuid_list = "\nuuid:".join(x for x in missing_uuids)
        assert False, f"bookmarks exist in Elasticsearch but not in database, \nuuid:{uuid_list}"


def test_bookmark_fields_are_trimmed():
    "Assert that bookmark fields have no leading or trailing whitespace"

    bookmarks = Bookmark.objects.filter(
        Q(url__iregex=r"\s$")
        | Q(url__iregex=r"^\s")
        | Q(name__iregex=r"\s$")
        | Q(name__iregex=r"^\s")
        | Q(note__iregex=r"\s$")
        | Q(note__iregex=r"^\s")
    )
    assert len(bookmarks) == 0, f"{len(bookmarks)} fail this test; example: id={bookmarks[0].id}"


def test_bookmark_thumbnails_in_s3_exist_in_db():
    "Assert that all bookmark thumbanils in S3 also exist in the database"

    s3_resource = boto3.resource("s3")

    unique_uuids = set()

    paginator = s3_resource.meta.client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for key in page["Contents"]:
            m = re.search(r"^bookmarks/(\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)", str(key["Key"]))
            if m:
                unique_uuids.add(m.group(1))

    missing_uuids = []
    for key in unique_uuids:
        if not Bookmark.objects.filter(uuid=key).exists():
            missing_uuids.append(key)

    if missing_uuids:
        uuid_list = "\nuuid:".join(x for x in missing_uuids)
        assert False, f"bookmark thumbnails found in S3 but not in DB, \nuuid:{uuid_list}"
