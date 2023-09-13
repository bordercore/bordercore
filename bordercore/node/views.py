import json
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormMixin
from django.views.generic.list import ListView

from blob.models import RecentlyViewedBlob
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

        RecentlyViewedBlob.add(self.request.user, node=self.object)

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
    todo_list = node.get_todo_list()

    response = {
        "status": "OK",
        "todo_list": todo_list
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
    options = json.loads(request.POST.get("options", "{}"))

    node = Node.objects.get(uuid=node_uuid, user=request.user)

    # Choose a random quote
    quote = Quote.objects.all().order_by("?").first()
    node.add_quote(quote, options)

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def remove_quote(request):

    node_uuid = request.POST["node_uuid"]
    uuid = request.POST["uuid"]

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.remove_quote(uuid)

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def update_quote(request):

    node_uuid = request.POST["node_uuid"]
    uuid = request.POST["uuid"]
    options = json.loads(request.POST["options"])
    options["favorites_only"] = True if options.get("favorites_only", "false") == "true" else False

    node = Node.objects.get(uuid=node_uuid, user=request.user)
    node.update_quote(uuid, options)

    response = {
        "status": "OK",
        "layout": node.get_layout()
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


@login_required
def add_node(request):

    parent_node_uuid = request.POST["parent_node_uuid"]
    node_uuid = request.POST["node_uuid"]
    options = json.loads(request.POST.get("options", "{}"))

    node = Node.objects.get(uuid=parent_node_uuid, user=request.user)
    node.add_node(node_uuid, options)

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def remove_node(request):

    parent_node_uuid = request.POST["parent_node_uuid"]
    uuid = request.POST["uuid"]

    node = Node.objects.get(uuid=parent_node_uuid, user=request.user)
    node.remove_node(uuid)

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def update_node(request):

    parent_node_uuid = request.POST["parent_node_uuid"]
    uuid = request.POST["uuid"]
    options = json.loads(request.POST["options"])

    node = Node.objects.get(uuid=parent_node_uuid, user=request.user)
    node.update_node(uuid, options)

    response = {
        "status": "OK",
        "layout": node.get_layout()
    }

    return JsonResponse(response)


@login_required
def search(request):
    node_list = Node.objects.filter(name__icontains=request.GET["query"])

    response = [
        {
            "uuid": x.uuid,
            "name": x.name
        }
        for x in
        node_list
    ]

    return JsonResponse(response, safe=False)


@login_required
def node_preview(request, uuid):

    node = Node.objects.get(user=request.user, uuid=uuid)
    preview = node.get_preview()

    try:
        random_note = random.choice(preview["notes"])
    except IndexError:
        random_note = []

    try:
        random_todo = random.choice(preview["todos"])
    except IndexError:
        random_todo = []

    response = {
        "status": "OK",
        "info": {
            "uuid": uuid,
            "name": node.name,
            "images": preview["images"],
            "note_count": len(preview["notes"]),
            "random_note": random_note,
            "random_todo": random_todo,
            "todo_count": len(preview["todos"]),
        }
    }

    return JsonResponse(response)
