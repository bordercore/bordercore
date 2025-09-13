"""
Views for node creation, listing, detail display, and management of todos, notes, images, quotes, collections, and nested nodes.

This module defines class-based and function-based views for creating, listing,
and manipulating ``Node`` objects and their related components (todos, notes,
images, quotes, collections, and nested nodes).
"""

from __future__ import annotations

import json
import random
from typing import Any, Dict, cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import (HttpRequest, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormMixin
from django.views.generic.list import ListView

from blob.models import Blob, RecentlyViewedBlob
from collection.models import Collection
from lib.mixins import FormRequestMixin
from node.forms import NodeForm
from quote.models import Quote
from todo.models import Todo

from .models import Node, NodeTodo
from .services import get_node_list


@method_decorator(login_required, name="dispatch")
class NodeListView(ListView, FormMixin):
    """List view for a user's nodes.

    Renders a paginated list of ``Node`` objects for the authenticated user and
    provides a bound ``NodeForm`` on the page via ``FormMixin``.
    """

    form_class = NodeForm

    def get_queryset(self) -> Any:
        """Get the queryset of nodes for the current user.

        Returns:
            Queryset of ``Node`` objects filtered by user.
        """
        return get_node_list(self.request.user)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for the node list view.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            Dictionary containing context data for the template.
        """
        context = super().get_context_data(**kwargs)
        context["title"] = "Node List"
        return context


@method_decorator(login_required, name="dispatch")
class NodeDetailView(DetailView):
    """Detail view for a single node."""

    model = Node
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for the node detail view.

        Also populates derived fields on the ``Node`` instance for display.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            Dictionary containing context data for the template.
        """
        context = super().get_context_data(**kwargs)
        context["priority_list"] = json.dumps(Todo.PRIORITY_CHOICES)

        RecentlyViewedBlob.add(self.request.user, node=self.object)

        self.object.populate_names()
        self.object.populate_image_info()

        return context


@method_decorator(login_required, name="dispatch")
class NodeCreateView(FormRequestMixin, CreateView):
    """Create new nodes."""

    template_name = "node/node_list.html"
    form_class = NodeForm

    def form_valid(self, form: NodeForm) -> HttpResponse:
        """Process valid form submission for node creation.

        Args:
            form: The validated ``NodeForm``.

        Returns:
            HTTP redirect to the success URL.
        """
        node = form.save(commit=False)
        node.user = cast(User, self.request.user)
        node.save()

        # Save the tags
        form.save_m2m()

        messages.add_message(
            self.request,
            messages.INFO,
            f"New node created: <strong>{node.name}</strong>",
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return the URL to redirect to after successful creation.

        Returns:
            URL string for the node list page.
        """
        return reverse("node:list")


@login_required
def edit_note(request: HttpRequest) -> JsonResponse:
    """Update a node's freeform note.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with operation status.
    """
    node_uuid = request.POST["uuid"]
    note = request.POST["note"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.note = note
    node.save()

    response = {
        "status": "OK"
    }

    return JsonResponse(response)


@login_required
def get_todo_list(request: HttpRequest, uuid: str) -> JsonResponse:
    """Return the serialized todo list for a node.

    Args:
        request: The HTTP request object.
        uuid: Node UUID.

    Returns:
        Json response with ``todo_list`` payload and status.
    """
    user = cast(User, request.user)
    node = Node.objects.get(uuid=uuid, user=user)
    todo_list = node.get_todo_list()

    response: Dict[str, Any] = {"status": "OK", "todo_list": todo_list}
    return JsonResponse(response)


@login_required
def add_todo(request: HttpRequest) -> JsonResponse:
    """Attach a ``Todo`` to a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with operation status.
    """
    node_uuid: str = request.POST["node_uuid"]
    todo_uuid: str = request.POST["todo_uuid"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    todo = Todo.objects.get(uuid=todo_uuid)

    so = NodeTodo(node=node, todo=todo)
    so.save()

    so.node.modified = timezone.now()
    so.node.save()

    response: Dict[str, str] = {"status": "OK"}
    return JsonResponse(response)


@login_required
def remove_todo(request: HttpRequest) -> JsonResponse:
    """Detach a ``Todo`` from a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with operation status.
    """
    node_uuid: str = request.POST["node_uuid"]
    todo_uuid: str = request.POST["todo_uuid"]

    so = NodeTodo.objects.get(node__uuid=node_uuid, todo__uuid=todo_uuid)
    so.delete()

    so.node.modified = timezone.now()
    so.node.save()

    response: Dict[str, str] = {"status": "OK"}
    return JsonResponse(response)


@login_required
def sort_todos(request: HttpRequest) -> JsonResponse:
    """Reorder a node's todo item to a new position.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with operation status.
    """
    node_uuid: str = request.POST["node_uuid"]
    todo_uuid: str = request.POST["todo_uuid"]
    new_position: int = int(request.POST["new_position"])

    so = NodeTodo.objects.get(node__uuid=node_uuid, todo__uuid=todo_uuid)
    NodeTodo.reorder(so, new_position)

    so.node.modified = timezone.now()
    so.node.save()

    response: Dict[str, str] = {"status": "OK"}
    return JsonResponse(response)


@login_required
def change_layout(request: HttpRequest) -> JsonResponse:
    """Replace a node's layout JSON.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with operation status.
    """
    node_uuid: str = request.POST["node_uuid"]
    layout: str = request.POST["layout"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.layout = json.loads(layout)
    node.save()

    response: Dict[str, str] = {"status": "OK"}
    return JsonResponse(response)


@login_required
def add_collection(request: HttpRequest) -> JsonResponse:
    """Add a collection component to a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with new ``collection_uuid``, refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    collection_name: str = request.POST["collection_name"]
    collection_uuid: str | None = request.POST.get("collection_uuid", None)
    display: str = request.POST["display"]
    random_order: bool = request.POST.get("random_order") == "true"
    rotate: Any = request.POST.get("rotate", -1)
    limit_raw: str = request.POST.get("limit", "")
    limit: int | None = None if limit_raw.strip().lower() in ("", "null") else int(limit_raw)
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    collection = node.add_collection(
        collection_name, collection_uuid, display, rotate, random_order, limit
    )

    response: Dict[str, Any] = {
        "status": "OK",
        "collection_uuid": collection.uuid,
        "layout": node.get_layout(),
    }
    return JsonResponse(response)


@login_required
def update_collection(request: HttpRequest) -> JsonResponse:
    """Update collection metadata and node options.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with operation status.
    """
    node_uuid: str = request.POST["node_uuid"]
    collection_uuid: str = request.POST["collection_uuid"]
    name: str = request.POST["name"]
    display: str = request.POST["display"]
    random_order: bool = request.POST["random_order"] == "true"
    rotate: Any = request.POST["rotate"]
    limit: Any = request.POST["limit"]
    user = cast(User, request.user)

    collection = Collection.objects.get(uuid=collection_uuid)
    collection.name = name
    collection.save()

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.update_collection(collection_uuid, display, random_order, rotate, limit)

    response: Dict[str, str] = {"status": "OK"}
    return JsonResponse(response)


@login_required
def delete_collection(request: HttpRequest) -> JsonResponse:
    """Remove a collection component from a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    collection_uuid: str = request.POST["collection_uuid"]
    collection_type: str = request.POST["collection_type"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.delete_collection(collection_uuid, collection_type)

    response: Dict[str, Any] = {"status": "OK", "layout": node.get_layout()}
    return JsonResponse(response)


@login_required
def add_note(request: HttpRequest) -> JsonResponse:
    """Create a note component and set its color.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with new ``note_uuid``, refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    note_name: str = request.POST["note_name"]
    color: int = int(request.POST["color"])
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    note = node.add_note(note_name)

    node.set_note_color(str(note.uuid), color)

    response: Dict[str, Any] = {
        "status": "OK",
        "note_uuid": note.uuid,
        "layout": node.get_layout(),
    }
    return JsonResponse(response)


@login_required
def delete_note(request: HttpRequest) -> JsonResponse:
    """Delete a note component from a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    note_uuid: str = request.POST["note_uuid"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.delete_note(note_uuid)

    response: Dict[str, Any] = {"status": "OK", "layout": node.get_layout()}
    return JsonResponse(response)


@login_required
def set_note_color(request: HttpRequest) -> JsonResponse:
    """Set the color index for a note on a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with operation status.
    """
    node_uuid: str = request.POST["node_uuid"]
    note_uuid: str = request.POST["note_uuid"]
    color: int = int(request.POST["color"])
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.set_note_color(note_uuid, color)

    response: Dict[str, str] = {"status": "OK"}
    return JsonResponse(response)


@login_required
def add_image(request: HttpRequest) -> JsonResponse:
    """Add an image component to a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    image_uuid: str = request.POST["image_uuid"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    image = Blob.objects.get(uuid=image_uuid, user=user)
    node.add_component("image", image)

    node.populate_image_info()

    response: Dict[str, Any] = {"status": "OK", "layout": json.dumps(node.layout)}
    return JsonResponse(response)


@login_required
def add_quote(request: HttpRequest) -> JsonResponse:
    """Add a quote component to a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    options: Dict[str, Any] = json.loads(request.POST.get("options", "{}"))
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)

    # Choose a random quote
    quote = Quote.objects.all().order_by("?").first()
    if quote is None:
        return JsonResponse({"status": "error", "message": "No quotes available."}, status=404)

    node.add_component("quote", quote, options)

    response: Dict[str, Any] = {"status": "OK", "layout": node.get_layout()}
    return JsonResponse(response)


@login_required
def update_quote(request: HttpRequest) -> JsonResponse:
    """Update options for an existing quote component.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    uuid: str = request.POST["uuid"]
    options: Dict[str, Any] = json.loads(request.POST["options"])
    options["favorites_only"] = options.get("favorites_only", "false") == "true"
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.update_component(uuid, options)

    response: Dict[str, Any] = {"status": "OK", "layout": node.get_layout()}
    return JsonResponse(response)


@login_required
def get_quote(request: HttpRequest) -> JsonResponse:
    """Fetch a (possibly favorite-only) random quote and set it on the node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with selected quote payload and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    favorites_only: str = request.POST.get("favorites_only", "false")
    user = cast(User, request.user)

    quote_qs = Quote.objects.all()
    if favorites_only == "true":
        quote_qs = quote_qs.filter(is_favorite=True)
    quote = quote_qs.order_by("?")[0]

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.set_quote(quote.uuid)

    response: Dict[str, Any] = {
        "status": "OK",
        "quote": {
            "uuid": quote.uuid,
            "is_favorite": quote.is_favorite,
            "quote": quote.quote,
            "source": quote.source,
        },
    }
    return JsonResponse(response)


@login_required
def add_todo_list(request: HttpRequest) -> JsonResponse:
    """Create a todo list component for the node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.add_todo_list()

    response: Dict[str, Any] = {"status": "OK", "layout": node.get_layout()}
    return JsonResponse(response)


@login_required
def delete_todo_list(request: HttpRequest) -> JsonResponse:
    """Delete the todo list component from the node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.delete_todo_list()

    response: Dict[str, Any] = {"status": "OK", "layout": node.get_layout()}
    return JsonResponse(response)


@login_required
def add_node(request: HttpRequest) -> JsonResponse:
    """Nest an existing node as a component of another node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    parent_node_uuid: str = request.POST["parent_node_uuid"]
    node_uuid: str = request.POST["node_uuid"]
    options: Dict[str, Any] = json.loads(request.POST.get("options", "{}"))
    user = cast(User, request.user)

    parent_node = Node.objects.get(uuid=parent_node_uuid, user=user)
    node = Node.objects.get(uuid=node_uuid, user=user)
    parent_node.add_component("node", node, options)

    response: Dict[str, Any] = {"status": "OK", "layout": parent_node.get_layout()}
    return JsonResponse(response)


@login_required
def update_node(request: HttpRequest) -> JsonResponse:
    """Update options for a nested node component.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    parent_node_uuid: str = request.POST["parent_node_uuid"]
    uuid: str = request.POST["uuid"]
    options: Dict[str, Any] = json.loads(request.POST["options"])
    user = cast(User, request.user)

    node = Node.objects.get(uuid=parent_node_uuid, user=user)
    node.update_component(uuid, options)

    response: Dict[str, Any] = {"status": "OK", "layout": node.get_layout()}
    return JsonResponse(response)


@login_required
def search(request: HttpRequest) -> JsonResponse:
    """Search nodes by name.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with a list of objects with ``uuid`` and ``name``.
    """
    node_list = Node.objects.filter(name__icontains=request.GET["query"])

    response = [{"uuid": x.uuid, "name": x.name} for x in node_list]
    return JsonResponse(response, safe=False)


@login_required
def node_preview(request: HttpRequest, uuid: str) -> JsonResponse:
    """Return a lightweight preview payload for a node.

    Includes image UUIDs, counts, and random selections (when available) for
    notes and todos.

    Args:
        request: The HTTP request object.
        uuid: Node UUID.

    Returns:
        JSON response with ``info`` block for display and status.
    """
    user = cast(User, request.user)
    node = Node.objects.get(user=user, uuid=uuid)
    preview = node.get_preview()

    try:
        random_note = random.choice(preview["notes"])
    except IndexError:
        random_note = []

    try:
        random_todo = random.choice(preview["todos"])
    except IndexError:
        random_todo = []

    response: Dict[str, Any] = {
        "status": "OK",
        "info": {
            "uuid": uuid,
            "name": node.name,
            "images": preview["images"],
            "note_count": len(preview["notes"]),
            "random_note": random_note,
            "random_todo": random_todo,
            "todo_count": len(preview["todos"]),
        },
    }
    return JsonResponse(response)


@login_required
def remove_component(request: HttpRequest) -> JsonResponse:
    """Remove a component (by its component UUID) from a node.

    Args:
        request: The HTTP request object.

    Returns:
        JSON response with refreshed ``layout`` and status.
    """
    node_uuid: str = request.POST["node_uuid"]
    uuid: str = request.POST["uuid"]
    user = cast(User, request.user)

    node = Node.objects.get(uuid=node_uuid, user=user)
    node.remove_component(uuid)

    response: Dict[str, Any] = {"status": "OK", "layout": node.get_layout()}
    return JsonResponse(response)
