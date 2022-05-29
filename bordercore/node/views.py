import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormMixin
from django.views.generic.list import ListView

from blob.models import Blob
from bookmark.models import Bookmark
from collection.models import Collection
from lib.mixins import FormRequestMixin
from node.forms import NodeForm
from todo.models import Todo

from .models import (Node, SortOrderNodeBlob, SortOrderNodeBookmark,
                     SortOrderNodeTodo)
from .services import get_node_list


@method_decorator(login_required, name="dispatch")
class NodeListView(ListView, FormMixin):

    form_class = NodeForm

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
        context["priority_list"] = json.dumps(Todo.PRIORITY_CHOICES)

        # TODO: Optimize the ORM here by getting all Collection names in one query
        for column in self.object.layout:
            for row in column:
                if row["type"] == "collection":
                    row["name"] = Collection.objects.get(uuid=row["uuid"]).name

        return context


@method_decorator(login_required, name="dispatch")
class NodeCreateView(FormRequestMixin, CreateView):
    template_name = "node/node_list.html"
    form_class = NodeForm

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()

        # Save the tags
        form.save_m2m()

        messages.add_message(self.request, messages.INFO, f"New node created: <strong>{obj.name}</strong>")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("node:list")


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


@login_required
def get_todo_list(request, uuid):

    node = Node.objects.get(uuid=uuid, user=request.user)
    todo_list = list(node.todos.all().only("name", "uuid").order_by("sortordernodetodo__sort_order"))

    response = {
        "status": "OK",
        "todo_list": [
            {
                "name": x.name,
                "uuid": x.uuid,
                "note": x.note,
            }
            for x
            in todo_list]
    }

    return JsonResponse(response)


@login_required
def add_todo(request):

    node_uuid = request.POST["node_uuid"]
    todo_uuid = request.POST["todo_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    todo = Todo.objects.get(uuid=todo_uuid)

    so = SortOrderNodeTodo(node=node, todo=todo)
    so.save()

    so.node.modified = timezone.now()
    so.node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def remove_todo(request):

    node_uuid = request.POST["node_uuid"]
    todo_uuid = request.POST["todo_uuid"]

    so = SortOrderNodeTodo.objects.get(node__uuid=node_uuid, todo__uuid=todo_uuid)
    so.delete()

    so.node.modified = timezone.now()
    so.node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def sort_todos(request):
    """
    Move a given todo to a new position in a sorted list
    """

    node_uuid = request.POST["node_uuid"]
    todo_uuid = request.POST["todo_uuid"]
    new_position = int(request.POST["new_position"])

    so = SortOrderNodeTodo.objects.get(node__uuid=node_uuid, todo__uuid=todo_uuid)
    SortOrderNodeTodo.reorder(so, new_position)

    so.node.modified = timezone.now()
    so.node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def change_layout(request):

    node_uuid = request.POST["node_uuid"]
    layout = request.POST["layout"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.layout = json.loads(layout)
    node.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def add_collection(request):

    node_uuid = request.POST["node_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    collection = node.add_collection()

    response = {
        "status": "OK",
        "collection_uuid": collection.uuid,
        "layout": json.dumps(node.layout)
    }

    return JsonResponse(response)


@login_required
def delete_collection(request):

    node_uuid = request.POST["node_uuid"]
    collection_uuid = request.POST["collection_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.delete_collection(collection_uuid)

    response = {
        "status": "OK",
        "layout": json.dumps(node.layout)
    }

    return JsonResponse(response)
