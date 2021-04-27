import re
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateformat import format
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tag.models import SortOrderTagTodo, Tag
from todo.forms import TodoForm
from todo.models import Todo


@method_decorator(login_required, name="dispatch")
class TodoListView(ListView):

    model = Todo
    template_name = "todo/index.html"
    context_object_name = "info"

    def get_filter(self):

        return {
            "todo_filter_priority": self.request.session.get("todo_filter_priority", ""),
            "todo_filter_time": self.request.session.get("todo_filter_time", ""),
            "todo_filter_tag": self.request.session.get("todo_filter_tag", ""),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return {
            **context,
            "tags": Todo.get_todo_counts(self.request.user),
            "filter": self.get_filter()
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
                queryset = queryset.filter(priority=priority)
            if time:
                queryset = queryset.filter(created__gt=(timezone.now() - timedelta(days=int(time))))
            if tag_name:
                queryset = queryset.filter(tag__name=tag_name)

            queryset = queryset.order_by("name")

        elif tag_name:

            queryset = Tag.objects.get(user=self.request.user, name=tag_name).todos.all().order_by("sortordertagtodo__sort_order")

        else:

            queryset = Todo.objects.filter(user=self.request.user).order_by("-created")

        return queryset

    def get(self, request, *args, **kwargs):

        search_term = self.request.GET.get("search", None)

        if search_term:
            tasks = Todo.search(search_term, self.request.user.id)
        else:
            tasks = self.get_queryset().values()

        info = []

        for sort_order, todo in enumerate(tasks, 1):
            data = {
                "manual_order": "",
                "sort_order": sort_order,
                "name": re.sub("[\n\r\"]", "", todo["name"]),
                "priority": Todo.get_priority_name(todo["priority"]),
                "created": format(todo["created"], "Y-m-d"),
                "note": re.sub("[\n\r\"]", "", todo["note"] or ""),
                "url": todo["url"],
                "uuid": todo["uuid"]
            }

            # if todo.data:
            #     data = {**data, **todo.data}

            info.append(data)

        response = {
            "status": "OK",
            "todo_list": info
        }

        return JsonResponse(response)


@method_decorator(login_required, name='dispatch')
class TodoDetailView(UpdateView):
    model = Todo
    template_name = 'todo/update.html'
    form_class = TodoForm
    success_url = reverse_lazy('todo:list')
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in TodoForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav'] = 'todo'
        context['uuid'] = self.kwargs.get('uuid')
        context['action'] = 'Update'
        context['title'] = 'Todo Update :: {}'.format(self.object.name)
        context['tags'] = [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
        return context

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user)

    def form_valid(self, form):

        task = form.instance

        with transaction.atomic():

            # Keep track of the sort order of this task for each
            #  tag. Once we delete them and add them back,
            #  restore the original sort order using this hash
            todo_sort_order = {}

            for tag in task.tags.all():
                s = SortOrderTagTodo.objects.get(tag=tag, todo=task)
                todo_sort_order[tag.name] = s.sort_order
                s.delete()

            # Delete all existing tags
            task.tags.clear()

            # Then add the tags specified in the form
            for tag in form.cleaned_data['tags']:
                task.tags.add(tag)
                s = SortOrderTagTodo.objects.get(tag=tag, todo=task)
                # The tag won't be in todo_sort_order if we're
                #  adding it as new, so check for that.
                if tag.name in todo_sort_order:
                    s.reorder(todo_sort_order[tag.name])

        self.object = form.save()
        context = self.get_context_data(form=form)
        context["message"] = "Task updated"
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name='dispatch')
class TodoCreateView(CreateView):
    template_name = 'todo/update.html'
    form_class = TodoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav'] = 'todo'
        context['action'] = 'Create'
        context['title'] = 'Todo Create'
        if 'tagsearch' in self.request.GET:
            context['tags'] = [{'text': self.request.GET['tagsearch'], 'value': self.request.GET['tagsearch'], 'is_meta': False}]
        return context

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in TodoForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)

        obj.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('todo:list')


@method_decorator(login_required, name='dispatch')
class TodoDeleteView(DeleteView):
    template_name = 'todo/update.html'
    form_class = TodoForm
    model = Todo
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    # Verify that the user is the owner of the task
    def get_object(self, queryset=None):
        obj = super().get_object()
        if not obj.user == self.request.user:
            raise Http404
        return obj

    def get_success_url(self):
        return reverse('todo:list')


@login_required
def sort_todo(request):
    """
    Given an ordered list of todo items with a specified tag, move an
    item to a new position within that list
    """

    tag_name = request.POST["tag"]
    todo_uuid = request.POST["todo_uuid"]
    new_position = int(request.POST["position"])

    s = SortOrderTagTodo.objects.get(tag__name=tag_name, todo__uuid=todo_uuid)
    SortOrderTagTodo.reorder(s, new_position)

    return JsonResponse({"status": "OK"}, safe=False)
