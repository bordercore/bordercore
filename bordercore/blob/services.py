from collections import defaultdict

import humanize
from elasticsearch import Elasticsearch

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from blob.models import Blob
from lib.util import is_image, is_pdf


def get_recent_blobs(user, limit=10):
    """
    Return an annotated list of the most recently created blobs,
    along with counts of their doctypes.
    """

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
                                        "doctype": "blob"
                                    }
                                },
                                {
                                    "term": {
                                        "doctype": "document"
                                    }
                                },
                                {
                                    "term": {
                                        "doctype": "book"
                                    }
                                },
                            ]
                        }
                    },
                ]
            }
        },
        "sort": {"created_date": {"order": "desc"}},
        "from": 0, "size": limit,
        "_source": ["created_date", "size", "uuid"]
    }

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    doctypes = defaultdict(int)

    # Prefetch all matched blobs from the database in one query, rather
    #  than using a separate query for each one in the loop below.
    uuid_list = [x["_source"]["uuid"] for x in results["hits"]["hits"]]
    blob_list = Blob.objects.filter(uuid__in=uuid_list).prefetch_related("tags", "metadata_set")

    returned_blob_list = []

    for match in results["hits"]["hits"]:

        blob = next(x for x in blob_list if str(x.uuid) == match["_source"]["uuid"])
        delta = timezone.now() - blob.modified

        props = {
            "name": blob.name,
            "tags": blob.get_tags(),
            "url": reverse("blob:detail", kwargs={"uuid": blob.uuid}),
            "delta_days": delta.days,
            "uuid": blob.uuid,
            "doctype": blob.doctype,
        }

        if blob.content:
            props["content"] = blob.content[:10000]
            props["content_size"] = humanize.naturalsize(len(blob.content))

        if "size" in match["_source"]:
            props["content_size"] = humanize.naturalsize(match["_source"]["size"])

        if is_image(blob.file) or is_pdf(blob.file):
            props["cover_url"] = blob.get_cover_info(size="large", get_info=False).get("url", None)

        returned_blob_list.append(props)

        doctypes[blob.doctype] += 1
        doctypes["all"] = len(results["hits"]["hits"])

    return returned_blob_list, doctypes
