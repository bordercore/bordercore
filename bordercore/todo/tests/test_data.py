import pytest

import django
from django.conf import settings

from lib.util import get_elasticsearch_connection

pytestmark = pytest.mark.data_quality

django.setup()

from todo.models import Todo  # isort:skip
from tag.models import Tag  # isort:skip


@pytest.fixture()
def es():

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)
    yield es


def test_todo_tasks_in_db_exist_in_elasticsearch(es):
    "Assert that all todo tasks in the database exist in Elasticsearch"
    todo = Todo.objects.all().only("uuid")

    for task in todo:
        search_object = {
            "query": {
                "term": {
                    "uuid": task.uuid
                }
            },
            "_source": ["id"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"todo task found in the database but not in Elasticsearch, id={task.uuid}"


def test_todo_tags_match_elasticsearch(es):
    "Assert that all todo tags match those found in Elasticsearch"
    todo = Todo.objects.filter(tags__isnull=False).only("uuid", "tags")

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
                                "uuid": task.uuid
                            }
                        },
                        tag_query
                    ]
                }
            },
            "_source": ["id"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"todo's tags don't match those found in Elasticsearch, id={task.uuid}"


def test_elasticsearch_todo_tasks_exist_in_db(es):
    "Assert that all todo tasks in Elasticsearch exist in the database"

    search_object = {
        "query": {
            "term": {
                "doctype": "todo"
            }
        },
        "from": 0, "size": 10000,
        "_source": ["_id", "bordercore_id"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    for task in found:
        assert Todo.objects.filter(id=task["_source"]["bordercore_id"]).count() == 1, f"todo exists in Elasticsearch but not in database, id={task['_id']}"
