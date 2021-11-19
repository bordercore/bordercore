import pytest

import django
from django.conf import settings
from django.db.models import Q

from lib.util import get_elasticsearch_connection, get_missing_bookmark_ids

pytestmark = pytest.mark.data_quality

django.setup()

from bookmark.models import Bookmark  # isort:skip


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
        assert found["hits"]["total"]["value"] == batch_size, \
            "bookmarks found in the database but not in Elasticsearch: " + get_missing_bookmark_ids(bookmarks[batch:batch + step], found)


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

    for bookmark in found:
        assert Bookmark.objects.filter(uuid=bookmark["_source"]["uuid"]).count() == 1, \
            f"bookmark exists in Elasticsearch but not in database, uuid={bookmark['_source']['uuid']}"


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
