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

from collection.models import Collection
from lib.mixins import FormRequestMixin
from node.forms import NodeForm
from quote.models import Quote
from todo.models import Todo

from .models import Node, NodeTodo
from .services import get_node_list


@method_decorator(login_required, name="dispatch")
class NodeListView(ListView, FormMixin):

    form_class = NodeForm

    def get_queryset(self):
        return get_node_list(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nodes"] = context["object_list"]
        context["title"] = "Node List"

        return context


@method_decorator(login_required, name="dispatch")
class NodeDetailView(DetailView):

    model = Node
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["priority_list"] = json.dumps(Todo.PRIORITY_CHOICES)

        self.object.populate_names()
        self.object.populate_image_info()

        return context


@method_decorator(login_required, name="dispatch")
class NodeCreateView(FormRequestMixin, CreateView):
    template_name = "node/node_list.html"
    form_class = NodeForm

    def form_valid(self, form):

        node = form.save(commit=False)
        node.user = self.request.user
        node.save()

        # Save the tags
        form.save_m2m()

        messages.add_message(self.request, messages.INFO, f"New node created: <strong>{node.name}</strong>")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("node:list")


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
    todo_list = list(node.todos.all().only("name", "uuid").order_by("nodetodo__sort_order"))

    response = {
        "status": "OK",
        "todo_list": [
            {
                "name": x.name,
                "uuid": x.uuid,
                "note": x.note,
                "url": x.url,
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

    so = NodeTodo(node=node, todo=todo)
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

    so = NodeTodo.objects.get(node__uuid=node_uuid, todo__uuid=todo_uuid)
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

    so = NodeTodo.objects.get(node__uuid=node_uuid, todo__uuid=todo_uuid)
    NodeTodo.reorder(so, new_position)

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
    collection_name = request.POST["collection_name"]
    collection_uuid = request.POST.get("collection_uuid", None)
    display = request.POST["display"]
    random_order = True if request.POST["random_order"] == "true" else False
    rotate = request.POST.get("rotate", -1)
    limit = request.POST.get("limit", None)

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    collection = node.add_collection(collection_name, collection_uuid, display, rotate, random_order, limit)

    response = {
        "status": "OK",
        "collection_uuid": collection.uuid,
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def update_collection(request):

    node_uuid = request.POST["node_uuid"]
    collection_uuid = request.POST["collection_uuid"]
    name = request.POST["name"]
    display = request.POST["display"]
    random_order = True if request.POST["random_order"] == "true" else False
    rotate = request.POST["rotate"]
    limit = request.POST["limit"]

    collection = Collection.objects.get(uuid=collection_uuid)
    collection.name = name
    collection.save()

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.update_collection(collection_uuid, display, random_order, rotate, limit)

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def delete_collection(request):

    node_uuid = request.POST["node_uuid"]
    collection_uuid = request.POST["collection_uuid"]
    collection_type = request.POST["collection_type"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.delete_collection(collection_uuid, collection_type)

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def add_note(request):

    node_uuid = request.POST["node_uuid"]
    note_name = request.POST["note_name"]
    color = int(request.POST["color"])

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    note = node.add_note(note_name)

    node.set_note_color(str(note.uuid), color)

    response = {
        "status": "OK",
        "note_uuid": note.uuid,
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def delete_note(request):

    node_uuid = request.POST["node_uuid"]
    note_uuid = request.POST["note_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.delete_note(note_uuid)

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def set_note_color(request):

    node_uuid = request.POST["node_uuid"]
    note_uuid = request.POST["note_uuid"]
    color = int(request.POST["color"])

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.set_note_color(note_uuid, color)

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def add_image(request):

    node_uuid = request.POST["node_uuid"]
    image_uuid = request.POST["image_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.add_image(image_uuid)

    node.populate_image_info()

    response = {
        "status": "OK",
        "layout": json.dumps(node.layout)
    }

    return JsonResponse(response)


@login_required
def remove_image(request):

    node_uuid = request.POST["node_uuid"]
    image_uuid = request.POST["image_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.remove_image(image_uuid)

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def add_quote(request):

    node_uuid = request.POST["node_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)

    # Choose a random quote
    quote = Quote.objects.all().order_by("?")[0]
    node.add_quote(quote.uuid)

    response = {
        "status": "OK",
        "layout": json.dumps(node.layout)
    }

    return JsonResponse(response)


@login_required
def remove_quote(request):

    node_uuid = request.POST["node_uuid"]
    node_quote_uuid = request.POST["node_quote_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.remove_quote(node_quote_uuid)

    response = {
        "status": "OK",
        "layout": json.dumps(node.layout)
    }

    return JsonResponse(response)


@login_required
def update_quote(request):

    node_uuid = request.POST["node_uuid"]
    node_quote_uuid = request.POST["node_quote_uuid"]
    format = request.POST["format"]
    color = int(request.POST["color"])
    rotate = int(request.POST["rotate"])
    favorites_only = True if request.POST["favorites_only"] == "true" else False

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.update_quote(node_quote_uuid, color, format, rotate, favorites_only)

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


@login_required
def get_quote(request):

    node_uuid = request.POST["node_uuid"]
    favorites_only = request.POST.get("favorites_only", "false")

    quote = Quote.objects.all()
    if (favorites_only == "true"):
        quote = quote.filter(is_favorite=True)
    quote = quote.order_by("?")[0]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.set_quote(quote.uuid)

    response = {
        "status": "OK",
        "quote": {
            "uuid": quote.uuid,
            "is_favorite": quote.is_favorite,
            "quote": quote.quote,
            "source": quote.source
        },
    }

    return JsonResponse(response)


@login_required
def add_todo_list(request):

    node_uuid = request.POST["node_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.add_todo_list()

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def delete_todo_list(request):

    node_uuid = request.POST["node_uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.delete_todo_list()

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)
