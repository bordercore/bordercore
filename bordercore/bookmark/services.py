from urllib.parse import unquote

from django.conf import settings
from django.urls import reverse

from lib.util import get_elasticsearch_connection

from .models import Bookmark

SEARCH_LIMIT = 1000


def search(user, search_term):
    """
    Search for bookmarks in Elasticsearch based on a substring.
    """

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

    # Limit the search term to 10 characters, since we've configured the
    # Elasticsearch ngram_tokenizer to only analyze tokens up to that many
    # characters (see mappings.json). Otherwise no results will be returned
    # for longer terms.
    search_term = unquote(search_term.lower())[:10]

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
                            "doctype": "bookmark"
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
            "name",
            "url",
            "uuid",
        ]
    }

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    return [
        {
            "name": x["_source"]["name"],
            "url": x["_source"]["url"],
            "uuid": x["_source"]["uuid"],
            "favicon_url": Bookmark.get_favicon_url_static(x["_source"]["url"], size=16),
            "edit_url": reverse("bookmark:update", kwargs={"uuid": x["_source"]["uuid"]})
        }
        for x
        in
        results["hits"]["hits"]
    ]
