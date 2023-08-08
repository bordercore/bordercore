from elasticsearch import RequestError

from django.conf import settings
from django.contrib import messages

from lib.embeddings import len_safe_get_embedding
from lib.util import get_elasticsearch_connection


def semantic_search(request, search):

    embeddings = len_safe_get_embedding(search)

    search_object = {
        "query": {
            "function_score": {
                "functions": [
                    {
                        "script_score": {
                            "script": {
                                "source": "doc['embeddings_vector'].size() == 0 ? 0 : cosineSimilarity(params.query_vector, 'embeddings_vector') + 1.0",
                                "params": {
                                    "query_vector": embeddings
                                }
                            }
                        }
                    }
                ],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "user_id": request.user.id
                                }
                            },
                            {
                                "term": {
                                    "doctype": "note"
                                }
                            }
                        ]
                    }
                }
            }
        },
        "sort": {"_score": {"order": "desc"}},
        "size": 1,
        "_source": [
            "date",
            "contents",
            "doctype",
            "name",
            "title",
            "url",
            "uuid"
        ]
    }

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)
    try:
        return es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)
    except RequestError as e:
        messages.add_message(request, messages.ERROR, f"Request Error: {e.status_code} {e.info['error']}")
        return []
