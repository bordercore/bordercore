from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.utils.dateformat import format
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from todo.forms import TodoForm

from tag.models import Tag
from todo.models import Todo

SECTION = 'Todo'


@method_decorator(login_required, name='dispatch')
class TodoListView(ListView):

    model = Todo
    template_name = "todo/index.html"
    context_object_name = 'info'
    tagsearch = None

    def get_queryset(self):
        if 'tagsearch' in self.request.GET:
            tag = self.request.GET.get('tagsearch')
            self.request.session['current_todo_tag'] = tag
        elif 'current_todo_tag' in self.request.session:
            # Use the last tag accessed
            tag = Tag.objects.get(name=self.request.session.get('current_todo_tag')).name
        elif self.request.user.userprofile.todo_default_tag:
            tag = self.request.user.userprofile.todo_default_tag.name
        else:
            # TODO: get a random tag
            tag_info = Tag.objects.filter(todo__user=self.request.user, todo__isnull=False).distinct('name')
            tag = None
            if tag_info:
                tag = tag_info[0].name
        self.tagsearch = tag
        return Todo.objects.filter(user=self.request.user, tags__name=tag)

    def get_context_data(self, **kwargs):
        context = super(TodoListView, self).get_context_data(**kwargs)

        info = []

        for myobject in context['object_list']:
            info.append(dict(task=myobject.task, modified=myobject.get_modified(), unixtime=format(myobject.modified, 'U'), todoid=myobject.id))

        context['tags'] = Tag.objects.filter(todo__user=self.request.user, todo__isnull=False).distinct('name')
        context['tagsearch'] = self.tagsearch
        context['cols'] = ['task', 'modified', 'unixtime', 'todoid']
        context['section'] = SECTION
        context['info'] = info
        context['title'] = 'Todo List'
        return context


@method_decorator(login_required, name='dispatch')
class TodoDetailView(UpdateView):
    model = Todo
    template_name = 'todo/edit.html'
    form_class = TodoForm
    success_url = reverse_lazy('todo_list')

    def get_context_data(self, **kwargs):
        context = super(TodoDetailView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['pk'] = self.kwargs.get('pk')
        context['action'] = 'Edit'
        context['title'] = 'Todo Edit :: {}'.format(self.object.task)
        return context

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user)

    def form_valid(self, form):

        task = form.instance

        # Delete all existing tags
        task.tags.clear()

        # Then add the tags specified in the form
        for tag in form.cleaned_data['tags']:
            task.tags.add(tag)

        self.object = form.save()
        context = self.get_context_data(form=form)
        context["message"] = "Task updated"
        return HttpResponseRedirect(self.get_success_url())

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TodoDetailView, self).dispatch(*args, **kwargs)


@method_decorator(login_required, name='dispatch')
class TodoCreateView(CreateView):
    template_name = 'todo/edit.html'
    form_class = TodoForm

    def get_context_data(self, **kwargs):
        context = super(TodoCreateView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['action'] = 'Add'
        context['title'] = 'Todo Add'
        return context

    def get_form_kwargs(self):
        # pass the request object to the form so that we have access to the session
        kwargs = super(TodoCreateView, self).get_form_kwargs()
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
        return reverse('todo_list')


@login_required
def delete(request, todo_id=None):

    todo = Todo.objects.get(user=request.user, pk=todo_id)
    todo.delete()

    return JsonResponse("OK", safe=False)


@method_decorator(login_required, name='dispatch')
class TodoDeleteView(DeleteView):
    template_name = 'todo/edit.html'
    form_class = TodoForm
    model = Todo

    # Verify that the user is the owner of the task
    def get_object(self, queryset=None):
        obj = super(TodoDeleteView, self).get_object()
        if not obj.user == self.request.user:
            raise Http404
        return obj

    def get_success_url(self):
        return reverse('todo_list')
