"""
Views for managing Todo items, including HTML list display and JSON-based task APIs.

This module provides:
- `TodoListView`: Renders the main todo list page with filtering and context data.
- `TodoTaskList`: Returns a JSON list of todos based on query parameters or search.
- `sort_todo`, `move_to_top`, `reschedule_task`: Function-based views for AJAX task operations.
"""

import json
import re
from datetime import timedelta
from typing import Any, Dict, Optional

from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.http import HttpRequest, JsonResponse
from django.utils import dateformat, timezone
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from lib.util import get_field
from tag.models import Tag, TagTodo
from todo.models import Todo
from todo.services import search as search_service


@method_decorator(login_required, name="dispatch")
class TodoListView(ListView):
    """Render the main Todo page with filters, tags, and priority data."""

    model = Todo
    template_name = "todo/index.html"
    context_object_name = "info"

    def get_filter(self, tag: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Construct the current filter settings from session or URL tag.

        Args:
            tag: Optional tag name to force as the current filter.

        Returns:
            A dict with keys 'todo_filter_priority', 'todo_filter_time', and 'todo_filter_tag'.
        """
        return {
            "todo_filter_priority": self.request.session.get("todo_filter_priority", ""),
            "todo_filter_time": self.request.session.get("todo_filter_time", ""),
            "todo_filter_tag": tag or self.request.session.get("todo_filter_tag", ""),
        }

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add filter settings, tag counts, and UI data to template context.

        Args:
            **kwargs: Arbitrary keyword arguments passed from the base implementation.

        Returns:
            Context dict for rendering the template, including:
              - 'tags': list of tag/count pairs
              - 'filter': current filter settings
              - 'priority_list': JSON-stringified priority choices
              - 'title': page title
        """
        context = super().get_context_data(**kwargs)

        current_filter = self.get_filter()

        # If a uuid is given in the url, store the associated task and
        #  set one of its tags to be the filter. Also reset priority and
        #  time filters so that the task isn't filtered out.
        if "uuid" in self.kwargs:
            context["uuid"] = self.kwargs["uuid"]
            todo = Todo.objects.get(uuid=self.kwargs["uuid"])
            current_filter["todo_filter_tag"] = todo.tags.first()
            current_filter["todo_filter_priority"] = None
            current_filter["todo_filter_time"] = None

        return {
            **context,
            "tags": Todo.get_todo_counts(self.request.user),
            "filter": current_filter,
            "priority_list": json.dumps(Todo.PRIORITY_CHOICES),
            "title": "Todo"
        }


@method_decorator(login_required, name="dispatch")
class TodoTaskList(ListView):
    """Provide a JSON endpoint listing todos filtered by priority, time, tag, or search."""

    model = Todo
    context_object_name = "info"

    def get_queryset(self) -> QuerySet[Todo]:
        """Build a queryset of Todo objects based on GET parameters and session state.

        Reads 'priority', 'time', and 'tag' from request.GET, saves them in session,
        and filters the base Todo queryset accordingly.

        Returns:
            A Django QuerySet of filtered and ordered Todo instances.
        """
        priority = self.request.GET.get("priority", None)
        if priority is not None:
            self.request.session["todo_filter_priority"] = priority

        time = self.request.GET.get("time", None)
        if time is not None:
            self.request.session["todo_filter_time"] = time

        tag_name = self.request.GET.get("tag", None)
        if tag_name is not None:
            self.request.session["todo_filter_tag"] = tag_name

        if priority or time:

            queryset = Todo.objects.filter(user=self.request.user)

            if priority:
                queryset = queryset.filter(priority=int(priority))
            if time:
                queryset = queryset.filter(created__gt=(timezone.now() - timedelta(days=int(time))))
            if tag_name:
                queryset = queryset.filter(tag__name=tag_name)

            queryset = queryset.filter(nodetodo__isnull=True)
            queryset = queryset.order_by("name")

        elif tag_name:

            queryset = Tag.objects.get(
                user=self.request.user,
                name=tag_name
            ).todos.filter(
                nodetodo__isnull=True
            ).order_by(
                "tagtodo__sort_order"
            )

        else:

            queryset = Todo.objects.filter(
                user=self.request.user
            ).filter(
                nodetodo__isnull=True
            ).order_by(
                "-created"
            )

        queryset = queryset.prefetch_related("tags")

        return queryset

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle GET requests: return a JSON response with todo data and statistics.

        If 'search' is provided in request.GET, uses the search service; otherwise,
        uses the filtered queryset.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse containing:
              - 'status': always "OK"
              - 'priority_counts': list of (priority, count) tuples
              - 'created_counts': list of (date, count) tuples
              - 'todo_list': list of dicts with fields for each todo
        """
        search_term = self.request.GET.get("search", None)

        if search_term:
            tasks = search_service(self.request.user, search_term)
        else:
            tasks = self.get_queryset()
        info = []

        for sort_order, todo in enumerate(tasks, 1):
            data = {
                "manual_order": "",
                "sort_order": sort_order,
                "name": re.sub("[\n\r\"]", "", get_field(todo, "name")),
                "priority": get_field(todo, "priority"),
                "priority_name": Todo.get_priority_name(get_field(todo, "priority")),
                "created": dateformat.format(get_field(todo, "created"), "Y-m-d"),
                "created_unixtime": dateformat.format(get_field(todo, "created"), "U"),
                "note": get_field(todo, "note") or "",
                "url": get_field(todo, "url"),
                "uuid": get_field(todo, "uuid"),
                "due_date": get_field(todo, "due_date"),
                "tags": get_field(todo, "tags")
            }

            info.append(data)

        priority_counts = Todo.objects.priority_counts(request.user)
        created_counts = Todo.objects.created_counts(request.user)

        response = {
            "status": "OK",
            "priority_counts": list(priority_counts),
            "created_counts": list(created_counts),
            "todo_list": info
        }

        return JsonResponse(response)


@login_required
def sort_todo(request: HttpRequest) -> JsonResponse:
    """Reorder a Todo within its tag-specific list and return status.

    Expects POST parameters:
      - 'tag': name of the tag
      - 'todo_uuid': UUID of the todo
      - 'position': new integer position

    Args:
        request: The HTTP request with POST data.

    Returns:
        JsonResponse with {"status": "OK"}.
    """
    tag_name = request.POST["tag"]
    todo_uuid = request.POST["todo_uuid"]
    new_position = int(request.POST["position"])

    s = TagTodo.objects.get(tag__name=tag_name, todo__uuid=todo_uuid)
    TagTodo.reorder(s, new_position)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def move_to_top(request: HttpRequest) -> JsonResponse:
    """Move a Todo to the top position in its tag list.

    Modifies request.POST to set 'position' to 1 and delegates to `sort_todo`.

    Args:
        request: The HTTP request.

    Returns:
        JsonResponse from `sort_todo`, indicating success.
    """
    mutable_post = request.POST.copy()
    mutable_post["position"] = "1"
    request.POST = mutable_post
    return sort_todo(request)


@login_required
def reschedule_task(request: HttpRequest) -> JsonResponse:
    """Set a Todo's due date to one day from now and save.

    Expects POST parameter:
      - 'todo_uuid': UUID of the todo to reschedule.

    Args:
        request: The HTTP request with POST data.

    Returns:
        JsonResponse with {"status": "OK"}.
    """
    todo_uuid = request.POST["todo_uuid"]

    todo = Todo.objects.get(uuid=todo_uuid)
    todo.due_date = timezone.now() + timedelta(days=1)
    todo.save()

    return JsonResponse({"status": "OK"}, safe=False)
