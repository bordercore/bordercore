import json
import re
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateformat import format
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from tag.models import Tag, TagTodo
from todo.models import Todo
from todo.services import search as search_service


@method_decorator(login_required, name="dispatch")
class TodoListView(ListView):

    model = Todo
    template_name = "todo/index.html"
    context_object_name = "info"

    def get_filter(self, tag=None):

        return {
            "todo_filter_priority": self.request.session.get("todo_filter_priority", ""),
            "todo_filter_time": self.request.session.get("todo_filter_time", ""),
            "todo_filter_tag": tag or self.request.session.get("todo_filter_tag", ""),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filter = self.get_filter()

        # If a uuid is given in the url, store the associated task and
        #  set one of its tags to be the filter. Also reset priority and
        #  time filters so that the task isn't filtered out.
        if "uuid" in self.kwargs:
            context["uuid"] = self.kwargs["uuid"]
            todo = Todo.objects.get(uuid=self.kwargs["uuid"])
            filter["todo_filter_tag"] = todo.tags.first()
            filter["todo_filter_priority"] = None
            filter["todo_filter_time"] = None

        return {
            **context,
            "tags": Todo.get_todo_counts(self.request.user),
            "filter": filter,
            "priority_list": json.dumps(Todo.PRIORITY_CHOICES),
            "title": "Todo"
        }


@method_decorator(login_required, name="dispatch")
class TodoTaskList(ListView):

    model = Todo
    context_object_name = "info"

    def get_queryset(self):

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

    def get_field(self, object, field_name):

        if type(object) is dict:
            if field_name in object:
                return object[field_name]
            else:
                return [] if field_name == "tags" else None
        else:
            if field_name == "tags":
                return [x.name for x in object.tags.all()]
            else:
                return getattr(object, field_name)

    def get(self, request, *args, **kwargs):

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
                "name": re.sub("[\n\r\"]", "", self.get_field(todo, "name")),
                "priority": self.get_field(todo, "priority"),
                "priority_name": Todo.get_priority_name(self.get_field(todo, "priority")),
                "created": format(self.get_field(todo, "created"), "Y-m-d"),
                "note": self.get_field(todo, "note") or "",
                "url": self.get_field(todo, "url"),
                "uuid": self.get_field(todo, "uuid"),
                "due_date": self.get_field(todo, "due_date"),
                "tags": self.get_field(todo, "tags")
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
def sort_todo(request):
    """
    Given an ordered list of todo items with a specified tag, move an
    item to a new position within that list
    """

    tag_name = request.POST["tag"]
    todo_uuid = request.POST["todo_uuid"]
    new_position = int(request.POST["position"])

    s = TagTodo.objects.get(tag__name=tag_name, todo__uuid=todo_uuid)
    TagTodo.reorder(s, new_position)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def move_to_top(request):
    """
    Move a task to the top of the list.
    """
    mutable_post = request.POST.copy()
    mutable_post["position"] = 1
    request.POST = mutable_post
    return sort_todo(request)


@login_required
def reschedule_task(request):
    """
    Set the due date for a task to a day from now.
    """

    todo_uuid = request.POST["todo_uuid"]

    todo = Todo.objects.get(uuid=todo_uuid)
    todo.due_date = timezone.now() + timedelta(days=1)
    todo.save()

    return JsonResponse({"status": "OK"}, safe=False)
