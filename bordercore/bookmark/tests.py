import pytest
from elasticsearch import Elasticsearch

import django
from django.conf import settings

from lib.util import get_missing_bookmark_ids

django.setup()

from bookmark.models import Bookmark  # isort:skip


@pytest.fixture()
def es():

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        timeout=120,
        verify_certs=False
    )

    yield es


def test_bookmark_tags_match_elasticsearch_bulk(es):
    "Assert that all bookmarks tags match those found in Elasticsearch"
    bookmarks = Bookmark.objects.filter(tags__isnull=False).only("id", "tags").order_by("id").distinct("id")

    step = 50
    for batch in range(0, len(bookmarks), step):
        batch_size = len(bookmarks[batch:batch + step])

        query = [
            {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "_id": f"bordercore_bookmark_{b.id}"
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
            "_source": [""]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
        assert found["hits"]["total"]["value"] == batch_size, \
            "bookmark's tags don't match those found in Elasticsearch: " + get_missing_bookmark_ids(bookmarks[batch:batch + step], found)


def test_elasticsearch_bookmarks_exist_in_db(es):
    "Assert that all bookmarks in Elasticsearch exist in the database"

    search_object = {
        "query": {
            "term": {
                "doctype": f"bordercore_bookmark"
            }
        },
        "from": 0, "size": 10000,
        "_source": ["_id", "bordercore_id"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    for bookmark in found:
        assert Bookmark.objects.filter(id=bookmark["_source"]["bordercore_id"]).count() == 1, \
            f"bookmark exists in Elasticsearch but not in database, id={bookmark['_id']}"
