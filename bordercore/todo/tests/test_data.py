import pytest
from elasticsearch import Elasticsearch

import django
from django.conf import settings
from django.db.models import Count, Max, Min, Q

pytestmark = pytest.mark.data_quality

django.setup()

from todo.models import Todo, TagTodoSortOrder  # isort:skip
from tag.models import Tag  # isort:skip

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
    todo = Todo.objects.all().only("uuid")

    for task in todo:
        search_object = {
            "query": {
                "term": {
                    "uuid.keyword": task.uuid
                }
            },
            "_source": ["id"]
        }

        found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["total"]["value"]
        assert found == 1, f"todo task found in the database but not in Elasticsearch, id={task.id}"


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
                                "uuid.keyword": task.uuid
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
                "doctype": f"todo"
            }
        },
        "from": 0, "size": 10000,
        "_source": ["_id", "bordercore_id"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    for task in found:
        assert Todo.objects.filter(id=task["_source"]["bordercore_id"]).count() == 1, f"todo exists in Elasticsearch but not in database, id={task['_id']}"


def test_todo_sort_order():
    """
    This test checks for three things:

    For every user, min(sort_order) = 1
    For every user, max(sort_order) should equal the total count
    No duplicate sort_order values for each user
    """
    tags = Tag.objects.filter(Q(todo__isnull=False)).distinct("name")

    for tag in tags:

        count = TagTodoSortOrder.objects.filter(tag_todo__tag=tag).count()
        if count > 0:
            assert TagTodoSortOrder.objects.filter(tag_todo__tag=tag).aggregate(Min("sort_order"))["sort_order__min"] == 1, f"Min(sort_order) is not 1 for todo tag={tag}"
            assert TagTodoSortOrder.objects.filter(tag_todo__tag=tag).aggregate(Max("sort_order"))["sort_order__max"] == count, f"Max(sort_order) does not equal total count for todo tag={tag}"

            q = TagTodoSortOrder.objects.values("sort_order", "tag_todo").order_by().annotate(dcount=Count("sort_order")).filter(dcount__gt=1)
            assert len(q) == 0, f"Multiple sort_order values found for tag={tag}"
