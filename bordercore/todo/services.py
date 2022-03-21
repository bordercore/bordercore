import datetime
from urllib.parse import unquote

from django.conf import settings

from lib.util import get_elasticsearch_connection

SEARCH_LIMIT = 1000


def search(user, todo_name):
    """
    Search for artists in Elasticsearch based on a substring.
    """

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

    search_term = unquote(todo_name.lower())

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": user.id
                        }
                    },
                    {
                        "term": {
                            "doctype": "todo"
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "match": {
                                        "name.autocomplete": {
                                            "query": search_term,
                                            "operator": "and"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "from": 0,
        "size": SEARCH_LIMIT,
        "_source": [
            "date",
            "last_modified",
            "name",
            "note",
            "priority",
            "tags",
            "url",
            "uuid"
        ]
    }

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    return [
        {
            "created": datetime.datetime.strptime(x["_source"]["date"]["gte"], "%Y-%m-%d %H:%M:%S"),
            "name": x["_source"]["name"],
            "note": x["_source"]["note"],
            "priority": x["_source"]["priority"],
            "tags": x["_source"]["tags"],
            "url": x["_source"]["url"],
            "uuid": x["_source"]["uuid"],
        }
        for x
        in
        results["hits"]["hits"]
    ]
