from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils.dateformat import format
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from tag.models import SortOrderTagTodo, Tag
from todo.forms import TodoForm
from todo.models import Todo


@method_decorator(login_required, name='dispatch')
class TodoListView(ListView):

    model = Todo
    template_name = "todo/index.html"
    context_object_name = 'info'
    tagsearch = None

    def get_queryset(self):
        if 'tagsearch' in self.request.GET:
            tag_name = self.request.GET.get('tagsearch')
            self.request.session['current_todo_tag'] = tag_name
        elif 'current_todo_tag' in self.request.session:
            # Use the last tag accessed
            tag_name = self.request.session.get('current_todo_tag')
        else:
            tag_info = Tag.objects.filter(user=self.request.user, todo__user=self.request.user, todo__isnull=False).first()
            tag_name = None
            if tag_info:
                tag_name = tag_info.name
        self.tagsearch = tag_name

        if tag_name:
            return Tag.objects.get(user=self.request.user, name=tag_name).todos.all().order_by("sortordertagtodo__sort_order")
        else:
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        info = []
        fields = []

        context["tags"] = Todo.get_todo_counts(self.request.user, self.tagsearch)

        for sort_order, todo in enumerate(context['object_list'], 1):

            data = dict(manual_order="",
                        sort_order=sort_order,
                        task=todo.task,
                        priority=Todo.get_priority_name(todo.priority),
                        modified=todo.get_modified(),
                        unixtime=format(todo.modified, 'U'),
                        uuid=todo.uuid)

            if todo.data:
                fields.extend(list(todo.data.keys()))
                data = {**data, **todo.data}

            info.append(data)

        fields = list(set(fields))

        context['tagsearch'] = self.tagsearch

        # These fields go first so we can easily reference
        #  them in the template by index
        context['cols'] = ['Manual', 'sort_order', 'unixtime', 'uuid']

        # Add the optional "data" JSONField fields
        context['cols'].extend(fields)

        context['cols'].extend(['task', 'priority', 'modified'])

        context['nav'] = 'todo'
        context['info'] = info
        context['title'] = 'Todo List'
        return context


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

            for tag in task.tags.all():
                s = SortOrderTagTodo.objects.get(tag=tag, todo=task)
                s.delete()

            # Delete all existing tags
            task.tags.clear()

            # Then add the tags specified in the form
            for tag in form.cleaned_data['tags']:
                task.tags.add(tag)

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
    Given an ordered list of bookmarks with a specified tag, move a
    bookmark to a new position within that list
    """

    tag_name = request.POST["tag"]
    todo_uuid = request.POST["todo_uuid"]
    new_position = int(request.POST["position"])

    s = SortOrderTagTodo.objects.get(tag__name=tag_name, todo__uuid=todo_uuid)
    SortOrderTagTodo.reorder(s, new_position)

    return JsonResponse({"status": "OK"}, safe=False)
