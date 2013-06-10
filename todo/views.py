from django.views.generic.list import ListView

from tag.models import Tag
from todo.models import Todo

SECTION = 'Todo'

class TodoListView(ListView):

    model = Todo
    template_name = "todo/index.html"
    paginate_by = 15
    context_object_name = 'info'
    tagsearch = None

    def get_queryset(self):
        if 'tagsearch' in self.request.GET:
            tag = self.request.GET.get('tagsearch')
        elif self.request.user.userprofile.todo_default_tag:
            tag = self.request.user.userprofile.todo_default_tag.name
        else:
            # TODO: get a random tag
            tag = Tag.objects.filter(todo__isnull=False).distinct('name')[0].name
        self.tagsearch = tag
        return Todo.objects.filter(user=self.request.user, tags__name=tag)

    def get_context_data(self, **kwargs):
        context = super(TodoListView, self).get_context_data(**kwargs)

        info = []

        for object in kwargs['object_list']:
            info.append( dict(task=object.task, modified=object.modified) )

        context['tags'] = Tag.objects.filter(todo__isnull=False).distinct('name')
        context['tagsearch'] = self.tagsearch
        context['cols'] = ['task', 'modified']
        context['section'] = SECTION
        context['info'] = info
        return context
