from urllib.parse import unquote

from django.conf import settings
from django.urls import reverse

from drill.models import Question
from lib.util import get_elasticsearch_connection

from .models import TagAlias

SEARCH_LIMIT = 1000


def get_additional_info(doc_types, user, tag_name):
    """
    Return additional information for each search result
    based on the doctypes.
    """

    if "drill" in doc_types:
        return {
            "info": Question.get_tag_progress(user, tag_name),
            "link": reverse("drill:start_study_session_tag", kwargs={"tag": tag_name})
        }
    return {}


def get_tag_link(tag, doc_types=[]):

    if "note" in doc_types:
        return reverse("search:notes") + f"?tagsearch={tag}"
    if "bookmark" in doc_types:
        return reverse("bookmark:overview") + f"?tag={tag}"
    if "drill" in doc_types:
        return reverse("drill:start_study_session_tag", kwargs={"tag": tag})
    if "song" in doc_types or "albunm" in doc_types:
        return reverse("music:search_tag") + f"?tag={tag}"

    return reverse("search:kb_search_tag_detail", kwargs={"taglist": tag})


def get_tag_aliases(user, name, doc_types=[]):

    tag_aliases = TagAlias.objects.filter(name__contains=name).select_related("tag")

    # Some fields contain the same value since two different searches call
    #  this method and expect different field names for the same data.
    return [
        {
            "doctype": "Tag",
            "text": x.tag.name,
            "id": f"{x.name} -> {x.tag}",
            "display": f"{x.name} -> {x.tag}",
            "name": f"{x.name} -> {x.tag}",
            "link": get_tag_link(x.tag.name, doc_types),
            **get_additional_info(doc_types, user, x.tag.name)
        }
        for x in
        tag_aliases
    ]


def search(user, tag_name, doc_types=[], skip_tag_aliases=False):
    """
    Search for tags attached to objects based on a substring in Elasticsearch.
    Optionally limit the search to objects of a specific doctype.
    """

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

    tag_name = tag_name.lower()

    search_term = unquote(tag_name)

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
                        "bool": {
                            "should": [
                                {
                                    "match": {
                                        "tags.autocomplete": {
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
        "aggs": {
            "distinct_tags": {
                "terms": {
                    "field": "tags.keyword",
                    "size": SEARCH_LIMIT
                }
            }
        },
        "from": 0,
        "size": 0,
        "_source": ["tags"]
    }

    # If a doctype list is passed in, then limit our search to tags attached
    #  to those particular object types, rather than to all tags.
    for doc_type in doc_types:
        search_object["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": doc_type
                }
            },
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    matches = []
    for tag_result in results["aggregations"]["distinct_tags"]["buckets"]:
        if tag_result["key"].lower().find(tag_name) != -1:
            matches.append(
                {
                    "label": tag_result["key"],
                    **get_additional_info(doc_types, user, tag_result["key"])
                }
            )

    if not skip_tag_aliases:
        matches.extend(get_tag_aliases(user, search_term, doc_types))

    return matches


def find_related_tags(user, tag_name, doc_type):
    """
    For a given tag, find the tag counts of all other documents
    which also have this tag for a given doc type.
    """

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

    tag_name = unquote(tag_name.lower())

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": 1
                        }
                    },
                    {
                        "term": {
                            "tags.keyword": tag_name
                        }
                    }
                ]
            }
        },
        "aggs": {
            "distinct_tags": {
                "terms": {
                    "field": "tags.keyword",
                }
            }
        },
        "from": 0,
        "size": 0,
        "_source": ["tags"]
    }

    if doc_type:
        search_object["query"]["bool"]["must"].append(
            {
                "term": {
                    "doctype": doc_type
                }
            }
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    matches = []
    for tag_result in results["aggregations"]["distinct_tags"]["buckets"]:
        if tag_result["key"] != tag_name:
            matches.append(
                {
                    "tag_name": tag_result["key"],
                    "count": tag_result["doc_count"]
                }
            )

    return matches
