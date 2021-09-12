from urllib.parse import unquote

from elasticsearch import Elasticsearch

from django.conf import settings
from django.urls import reverse

from blob.models import Blob

SEARCH_LIMIT = 1000


def search(user, todo_name):
    """
    Search for blobs by name
    """

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

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
                        "bool": {
                            "should": [
                                {
                                    "term": {
                                        "doctype": "book"
                                    }
                                },
                                {
                                    "term": {
                                        "doctype": "blob"
                                    }
                                },
                                {
                                    "term": {
                                        "doctype": "document"
                                    }
                                },
                            ]
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
        "_source": ["author",
                    "date",
                    "date_unixtime",
                    "doctype",
                    "filename",
                    "importance",
                    "name",
                    "note",
                    "sha1sum",
                    "tags",
                    "uuid"]
    }

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    return [
        {
            "doctype": x["_source"].get("doctype", ""),
            "note": x["_source"].get("note", ""),
            "name": x["_source"]["name"],
            "uuid": x["_source"].get("uuid"),
            "url": reverse('blob:detail', kwargs={"uuid": str(x["_source"].get("uuid"))}),
            "cover_url": settings.MEDIA_URL + Blob.get_cover_info(
                x["_source"].get("uuid"),
                x["_source"].get("filename"),
                size="small"
            )["url"]
        }
        for x
        in
        results["hits"]["hits"]
    ]
