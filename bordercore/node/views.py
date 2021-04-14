import re
import urllib

import markdown
from elasticsearch import Elasticsearch
from markdown.extensions.codehilite import CodeHiliteExtension

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from blob.models import Blob
from bookmark.models import Bookmark

from .models import Node, SortOrderNodeBlob, SortOrderNodeBookmark


class NodeOverviewView(TemplateView):

    template_name = "node/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nodes"] = Node.objects.filter(user=self.request.user)

        return context


@method_decorator(login_required, name="dispatch")
class NodeDetailView(DetailView):

    model = Node
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["node_uuid"] = self.object.uuid

        return context


@login_required
def get_blob_list(request, uuid):

    node = Node.objects.get(uuid=uuid, user=request.user)
    blob_list = list(node.blobs.all().only("title", "uuid").order_by("sortordernodeblob__sort_order"))

    response = {
        "status": "OK",
        "blob_list": [
            {
                "title": x.title,
                "url": reverse('blob:detail', kwargs={"uuid": str(x.uuid)}),
                "uuid": x.uuid,
                "note": x.sortordernodeblob_set.get(node=node).note,
                "cover_url": Blob.get_cover_info_static(
                    request.user,
                    x.sha1sum,
                    size="small"
                )["url"]
            }
            for x
            in blob_list]
    }

    return JsonResponse(response)


@login_required
def sort_blobs(request):
    """
    Move a given blob to a new position in a sorted list
    """

    node_uuid = request.POST["node_uuid"]
    blob_uuid = request.POST["blob_uuid"]
    new_position = int(request.POST["new_position"])

    s = SortOrderNodeBlob.objects.get(node__uuid=node_uuid, blob__uuid=blob_uuid)
    SortOrderNodeBlob.reorder(s, new_position)

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def add_blob(request):

    node_uuid = request.POST["node_uuid"]
    blob_uuid = request.POST["blob_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    blob = Blob.objects.get(uuid=blob_uuid, user=request.user)

    so = SortOrderNodeBlob(node=node, blob=blob)
    so.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def remove_blob(request):

    node_uuid = request.POST["node_uuid"]
    blob_uuid = request.POST["blob_uuid"]

    s = SortOrderNodeBlob.objects.get(node__uuid=node_uuid, blob__uuid=blob_uuid)
    s.delete()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def edit_blob_note(request):

    node_uuid = request.POST["node_uuid"]
    blob_uuid = request.POST["blob_uuid"]
    note = request.POST["note"]

    s = SortOrderNodeBlob.objects.get(node__uuid=node_uuid, blob__uuid=blob_uuid)
    s.note = note
    s.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def get_bookmark_list(request, uuid):

    node = Node.objects.get(uuid=uuid, user=request.user)
    bookmark_list = list(node.bookmarks.all().only("name", "id").order_by("sortordernodebookmark__sort_order"))

    response = {
        "status": "OK",
        "bookmark_list": [
            {
                "name": x.name,
                "url": x.url,
                "id": x.id,
                "favicon_url": x.get_favicon_url(size=16),
                "note": x.sortordernodebookmark_set.get(node=node).note,
            }
            for x
            in bookmark_list]
    }

    return JsonResponse(response)


@login_required
def sort_bookmarks(request):
    """
    Move a given bookmark to a new position in a sorted list
    """

    node_uuid = request.POST["node_uuid"]
    bookmark_id = request.POST["bookmark_id"]
    new_position = int(request.POST["new_position"])

    s = SortOrderNodeBookmark.objects.get(node__uuid=node_uuid, bookmark__id=bookmark_id)
    SortOrderNodeBookmark.reorder(s, new_position)

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def add_bookmark(request):

    node_uuid = request.POST["node_uuid"]
    bookmark_id = int(request.POST["bookmark_id"])

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    bookmark = Bookmark.objects.get(id=bookmark_id)

    so = SortOrderNodeBookmark(node=node, bookmark=bookmark)
    so.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def remove_bookmark(request):

    node_uuid = request.POST["node_uuid"]
    bookmark_id = request.POST["bookmark_id"]

    s = SortOrderNodeBookmark.objects.get(node__uuid=node_uuid, bookmark__id=bookmark_id)
    s.delete()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def edit_bookmark_note(request):

    node_uuid = request.POST["node_uuid"]
    bookmark_id = int(request.POST["bookmark_id"])
    note = request.POST["note"]

    s = SortOrderNodeBookmark.objects.get(node__uuid=node_uuid, bookmark__id=bookmark_id)
    s.note = note
    s.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def search_bookmarks(request):

    results = Bookmark.objects.filter(user=request.user).filter(name__icontains=request.GET["term"])
    matches = []

    for match in results:

        matches.append(
            {
                "id": match.id,
                "url": match.url,
                "note": match.note,
                "name": match.name,
                "favicon_url": match.get_favicon_url(size=16),
            }
        )

    return JsonResponse(matches, safe=False)


@login_required
def search_blob_titles(request):

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    search_term = request.GET["term"].lower()

    search_terms = re.split(r"\s+", urllib.parse.unquote(search_term))

    search_object = {
        "query": {
            "bool": {
                "must": [
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
                        "term": {
                            "user_id": request.user.id
                        }
                    }
                ]
            }
        },
        "from": 0, "size": 20,
        "_source": ["author",
                    "date",
                    "date_unixtime",
                    "doctype",
                    "filepath",
                    "importance",
                    "name",
                    "note",
                    "sha1sum",
                    "tags",
                    "title",
                    "uuid"]
    }

    # Separate query into terms based on whitespace and
    #  and treat it like an "AND" boolean search
    for one_term in search_terms:
        search_object["query"]["bool"]["must"].append(
            {
                "bool": {
                    "should": [
                        {
                            "wildcard": {
                                "title": {
                                    "value": f"*{one_term}*",
                                }
                            }
                        }
                    ]
                }
            }
        )

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    matches = []
    for match in results["hits"]["hits"]:
        matches.append(
            {
                "doctype": match["_source"].get("doctype", ""),
                "note": match["_source"].get("note", ""),
                "title": match["_source"]["title"],
                "uuid": match["_source"].get("uuid"),
                "url": reverse('blob:detail', kwargs={"uuid": str(match["_source"].get("uuid"))}),
                "cover_url": settings.MEDIA_URL + Blob.get_cover_info_static(
                    request.user,
                    match["_source"].get("sha1sum"),
                    size="small"
                )["url"]
            }
        )

    return JsonResponse(matches, safe=False)


@login_required
def get_note(request, uuid):

    node = Node.objects.get(uuid=uuid, user=request.user)

    node_html = markdown.markdown(node.note, extensions=[CodeHiliteExtension(guess_lang=False), "tables"]) if node.note else None

    response = {
        "status": "OK",
        "note": node.note,
        "noteHtml": node_html
    }

    return JsonResponse(response)


@login_required
def edit_note(request):

    node_uuid = request.POST["node_uuid"]
    note = request.POST["note"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.note = note
    node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)
