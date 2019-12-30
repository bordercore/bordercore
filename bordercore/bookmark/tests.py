import os

import django
from django.conf import settings
from elasticsearch import Elasticsearch
import pytest

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"

django.setup()

from bookmark.models import Bookmark


@pytest.fixture()
def es():

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        timeout=120,
        verify_certs=False
    )

    yield es


def test_bookmarks_in_db_exist_in_elasticsearch(es):
    "Assert that all bookmarks in the database exist in Elasticsearch"
    bookmarks = Bookmark.objects.all().only("id")

    for b in bookmarks:
        search_object = {
            "query": {
                "term": {
                    "_id": f"bordercore_bookmark_{b.id}"
                }
            },
            "_source": ["id"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"bookmark found in the database but not in Elasticsearch, id={b.id}"


def test_bookmark_tags_match_elasticsearch(es):
    "Assert that all bookmarks tags match those found in Elasticsearch"
    bookmarks = Bookmark.objects.filter(tags__isnull=False).only("id", "tags")

    for b in bookmarks:
        tag_query = [
            {
                "term": {
                    "tags.keyword": x.name
                }
            }
            for x in b.tags.all()
        ]

        search_object = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "_id": f"bordercore_bookmark_{b.id}"
                            }
                        },
                        tag_query
                    ]
                }
            },
            "_source": ["id"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"bookmark's tags don't match those found in Elasticsearch, id={b.id}"


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
        assert Bookmark.objects.filter(id=bookmark["_source"]["bordercore_id"]).count() == 1, f"bookmark exists in Elasticsearch but not in database, id={bookmark.id}"
