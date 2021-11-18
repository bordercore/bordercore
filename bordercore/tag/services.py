from urllib.parse import unquote

from elasticsearch import Elasticsearch

from django.conf import settings
from django.db.models import Count
from django.urls import reverse

from drill.models import Question

from .models import Tag, TagAlias

SEARCH_LIMIT = 1000


def get_additional_info(doctype, user, tag_name):
    """
    Return additional information for each search result
    based on the doctype.
    """

    if doctype == "drill":
        return {
            "info": Question.get_tag_progress(user, tag_name),
            "link": reverse("drill:start_study_session_tag", kwargs={"tag": tag_name})
        }
    return {}


def get_tag_link(doc_type, tag):

    if doc_type == "note":
        return reverse("search:notes") + f"?tagsearch={tag}"
    if doc_type == "bookmark":
        return reverse("bookmark:overview") + f"?tag={tag}"
    if doc_type == "drill":
        return reverse("drill:start_study_session_tag", kwargs={"tag": tag})
    if doc_type == "song" or doc_type == "album":
        return reverse("music:search_tag") + f"?tag={tag}"

    return reverse("search:kb_search_tag_detail", kwargs={"taglist": tag})


def get_tag_aliases(user, name, doc_type=None):

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
            "link": get_tag_link(doc_type, x.tag.name),
            **get_additional_info(doc_type, user, x.tag.name)
        }
        for x in
        tag_aliases
    ]


def get_random_tag_info(user):

    tag = Tag.objects.filter(user=user).order_by("?").first()

    info = Tag.objects.filter(name=tag.name) \
                      .annotate(
                          Count("blob", distinct=True),
                          Count("bookmark", distinct=True),
                          Count("album", distinct=True),
                          Count("collection", distinct=True),
                          Count("todo", distinct=True),
                          Count("question", distinct=True),
                          Count("song", distinct=True)
                      ).first()

    return info


def search(user, tag_name, doctype=None, skip_tag_aliases=False):
    """
    Search for tags attached to objects based on a substring in Elasticsearch.
    Optionally limit the search to objects of a specific doctype.
    """

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

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
    for tag_result in results["aggregations"]["distinct_tags"]["buckets"]:
        if tag_result["key"].lower().find(tag_name) != -1:
            matches.append(
                {
                    "display": tag_result["key"],
                    "text": tag_result["key"],
                    **get_additional_info(doctype, user, tag_result["key"])
                }
            )

    if not skip_tag_aliases:
        matches.extend(get_tag_aliases(user, search_term, doctype))

    return matches
