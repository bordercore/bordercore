from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from blob.models import Blob
from bookmark.models import Bookmark

from .models import Node, SortOrderNodeBlob, SortOrderNodeBookmark
from .services import get_node_list


@method_decorator(login_required, name="dispatch")
class NodeListView(ListView):

    def get_queryset(self):
        return get_node_list(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nodes"] = context["object_list"]

        return context


@method_decorator(login_required, name="dispatch")
class NodeDetailView(DetailView):

    model = Node
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@login_required
def get_blob_list(request, uuid):

    node = Node.objects.get(uuid=uuid, user=request.user)
    blob_list = list(node.blobs.all().only("name", "uuid").order_by("sortordernodeblob__sort_order"))

    response = {
        "status": "OK",
        "blob_list": [
            {
                "name": x.name,
                "url": reverse('blob:detail', kwargs={"uuid": str(x.uuid)}),
                "uuid": x.uuid,
                "note": x.sortordernodeblob_set.get(node=node).note,
                "cover_url": Blob.get_cover_url_static(
                    x.uuid,
                    x.file.name,
                    size="small"
                )
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

    so = SortOrderNodeBlob.objects.get(node__uuid=node_uuid, blob__uuid=blob_uuid)
    SortOrderNodeBlob.reorder(so, new_position)

    so.node.modified = timezone.now()
    so.node.save()

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

    so.node.modified = timezone.now()
    so.node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def remove_blob(request):

    node_uuid = request.POST["node_uuid"]
    blob_uuid = request.POST["blob_uuid"]

    so = SortOrderNodeBlob.objects.get(node__uuid=node_uuid, blob__uuid=blob_uuid)
    so.delete()

    so.node.modified = timezone.now()
    so.node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def edit_blob_note(request):

    node_uuid = request.POST["node_uuid"]
    blob_uuid = request.POST["blob_uuid"]
    note = request.POST["note"]

    so = SortOrderNodeBlob.objects.get(node__uuid=node_uuid, blob__uuid=blob_uuid)
    so.note = note
    so.save()

    so.node.modified = timezone.now()
    so.node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def add_bookmark(request):

    node_uuid = request.POST["node_uuid"]
    bookmark_uuid = request.POST["bookmark_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    bookmark = Bookmark.objects.get(uuid=bookmark_uuid)

    so = SortOrderNodeBookmark(node=node, bookmark=bookmark)
    so.save()

    so.node.modified = timezone.now()
    so.node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def get_note(request, uuid):

    node = Node.objects.get(uuid=uuid, user=request.user)

    response = {
        "status": "OK",
        "note": node.note
    }

    return JsonResponse(response)


@login_required
def edit_note(request):

    node_uuid = request.POST["uuid"]
    note = request.POST["note"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.note = note
    node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)
