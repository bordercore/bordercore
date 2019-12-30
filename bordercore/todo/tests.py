import os

import django
from django.conf import settings
from elasticsearch import Elasticsearch
import pytest

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
django.setup()

from todo.models import Todo


@pytest.fixture()
def es():

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        timeout=120,
        verify_certs=False
    )

    yield es


def test_todo_tasks_in_db_exist_in_elasticsearch(es):
    "Assert that all todo tasks in the database exist in Elasticsearch"
    todo = Todo.objects.all().only("id")

    for task in todo:
        search_object = {
            "query": {
                "term": {
                    "_id": f"bordercore_todo_{task.id}"
                }
            },
            "_source": ["id"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"todo task found in the database but not in Elasticsearch, id={task.id}"


def test_todo_tags_match_elasticsearch(es):
    "Assert that all todo tags match those found in Elasticsearch"
    todo = Todo.objects.filter(tags__isnull=False).only("id", "tags")

    for task in todo:
        tag_query = [
            {
                "term": {
                    "tags.keyword": x.name
                }
            }
            for x in task.tags.all()
        ]

        search_object = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "_id": f"bordercore_todo_{task.id}"
                            }
                        },
                        tag_query
                    ]
                }
            },
            "_source": ["id"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"todo's tags don't match those found in Elasticsearch, id={task.id}"


def test_elasticsearch_todo_tasks_exist_in_db(es):
    "Assert that all todo tasks in Elasticsearch exist in the database"

    search_object = {
        "query": {
            "term": {
                "doctype": f"bordercore_todo"
            }
        },
        "from": 0, "size": 10000,
        "_source": ["_id", "bordercore_id"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    for task in found:
        assert Todo.objects.filter(id=task["_source"]["bordercore_id"]).count() == 1, f"todo exists in Elasticsearch but not in database, id={task.id}"
