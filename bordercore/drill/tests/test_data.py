import pytest
from elasticsearch import Elasticsearch

import django
from django.conf import settings

from drill.models import Question
from lib.util import get_missing_blob_ids

pytestmark = pytest.mark.data_quality

django.setup()


@pytest.fixture()
def es():

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        timeout=120,
        verify_certs=False
    )

    yield es


def test_questions_in_db_exist_in_elasticsearch(es):
    "Assert that all questions in the database exist in Elasticsearch"

    questions = Question.objects.all().only("uuid")
    step_size = 100
    question_count = questions.count()

    for batch in range(0, question_count, step_size):
        # The batch_size will always be equal to "step_size", except probably
        #  the last batch, which will be less.
        batch_size = step_size if question_count - batch > step_size else question_count - batch

        query = [
            {
                "term": {
                    "_id": str(x.uuid)
                }
            }
            for x
            in questions[batch:batch + step_size]
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

        assert found["hits"]["total"]["value"] == batch_size,\
            "questions found in the database but not in Elasticsearch: " + get_missing_blob_ids(questions[batch:batch + step_size], found)


def test_elasticsearch_questions_exist_in_db(es):
    "Assert that all questions in Elasticsearch exist in the database"

    search_object = {
        "query": {
            "term": {
                "doctype": "drill"
            }
        },
        "from": 0, "size": 10000,
        "_source": ["_id", "bordercore_id"]
    }

    found = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)["hits"]["hits"]

    for question in found:
        assert Question.objects.filter(uuid=question["_id"]).count() == 1, \
            f"question exists in Elasticsearch but not in database, id={question['_id']}"
