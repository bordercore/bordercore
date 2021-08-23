import re
from urllib.parse import unquote

from elasticsearch import Elasticsearch

from django.conf import settings
from django.urls import reverse

from drill.models import Question

SEARCH_LIMIT = 1000


def get_additional_info(doctype, user, tag_result):
    """
    Return additional information for each search result
    based on the doctype.
    """

    if doctype == "drill":
        return {
            "info": Question.get_tag_progress(user, tag_result["key"]),
            "link": reverse("drill:start_study_session_tag", kwargs={"tag": tag_result["key"]})
        }
    return {}


def search(user, tag_name, doctype=None):
    """
    Search for tags attached to objects based on a substring in Elasticsearch.
    Optionally limit the search to objects of a specific doctype.
    """

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    tag_name = tag_name.lower()

    search_terms = re.split(r"\s+", unquote(tag_name))

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": user.id
                        }
                    },
                ]
            }
        },
        "aggs": {
            "Distinct Tags": {
                "terms": {
                    "field": "tags.keyword",
                    "size": SEARCH_LIMIT
                }
            }
        },
        "from": 0, "size": 0,
        "_source": ["tags"]
    }

    # Separate the query into terms based on whitespace and
    #  and treat it like an "AND" boolean search
    for one_term in search_terms:
        search_object["query"]["bool"]["must"].append(
            {
                "bool": {
                    "should": [
                        {
                            "wildcard": {
                                "tags": {
                                    "value": f"*{one_term}*",
                                }
                            }
                        }
                    ]
                }
            }
        )

    # If a doctype is passed in, then limit our search to tags attached
    #  to that particular object type, rather than to all tags.
    if doctype:
        search_object["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": doctype
                }
            },
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    matches = []
    for tag_result in results["aggregations"]["Distinct Tags"]["buckets"]:
        if tag_result["key"].lower().find(tag_name) != -1:
            matches.append(
                {
                    "value": tag_result["key"],
                    "text": tag_result["key"],
                    **get_additional_info(doctype, user, tag_result)
                }
            )

    return matches
