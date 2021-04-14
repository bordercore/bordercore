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

    def get_tag_name(self):

        if "tagsearch" in self.request.GET:
            tag_name = self.request.GET.get("tagsearch")
            self.request.session["current_todo_tag"] = tag_name
        elif "current_todo_tag" in self.request.session:
            # Use the last tag accessed
            tag_name = self.request.session.get("current_todo_tag")
        else:
            tag_info = Tag.objects.filter(user=self.request.user, todo__user=self.request.user, todo__isnull=False).first()
            tag_name = None
            if tag_info:
                tag_name = tag_info.name

        return tag_name

    def get_filter(self):

        return {
            "todo_filter_priority": self.request.session.get("todo_filter_priority", ""),
            "todo_filter_time": self.request.session.get("todo_filter_time", ""),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tag_name = self.get_tag_name()

        return {
            **context,
            "tags": Todo.get_todo_counts(self.request.user, tag_name),
            "tagsearch": tag_name,
            "filter": self.get_filter()
        }


@method_decorator(login_required, name="dispatch")
class TodoTaskList(ListView):

    model = Todo
    context_object_name = "info"

    def get_queryset(self):

        tag_name = self.kwargs.get("tag_name")
        self.request.session["current_todo_tag"] = tag_name

        priority = self.request.GET.get("priority", None)
        if priority is not None:
            self.request.session["todo_filter_priority"] = priority
        time = self.request.GET.get("time", None)
        if time is not None:
            self.request.session["todo_filter_time"] = time

        if priority or time:

            queryset = Todo.objects

            if priority:
                queryset = queryset.filter(priority=priority)
            if time:
                queryset = queryset.filter(created__gt=(timezone.now() - timedelta(days=int(time))))

            queryset = queryset.filter(tag__name=tag_name).order_by("task")

        else:
            queryset = Tag.objects.get(user=self.request.user, name=tag_name).todos.all().order_by("sortordertagtodo__sort_order")

        return queryset

    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        info = []
        fields = []

        for sort_order, todo in enumerate(queryset, 1):

            data = {
                "manual_order": "",
                "sort_order": sort_order,
                "task": re.sub("[\n\r\"]", "", todo.task),
                "priority": Todo.get_priority_name(todo.priority),
                "created": format(todo.modified, "Y-m-d"),
                "note": re.sub("[\n\r\"]", "", todo.get_note()),
                "url": todo.url,
                "uuid": todo.uuid
            }

            if todo.data:
                fields.extend(list(todo.data.keys()))
                data = {**data, **todo.data}

            info.append(data)

        fields = list(set(fields))

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
        context['title'] = 'Todo Update :: {}'.format(self.object.task)
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
