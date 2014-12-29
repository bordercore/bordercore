from django.contrib.auth.decorators import login_required
from django.utils.dateformat import format
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, Http404
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.core.urlresolvers import reverse

from blob.forms import BlobForm

from tag.models import Tag
from blob.models import Blob

SECTION = 'Blob'

class BlobListView(ListView):

    model = Blob
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
            tag = Tag.objects.filter(todo__isnull=False).distinct('name')[0].name
        self.tagsearch = tag
        return Blob.objects.filter(user=self.request.user, tags__name=tag)

    def get_context_data(self, **kwargs):
        context = super(BlobListView, self).get_context_data(**kwargs)
        info = []

        for myobject in context['object_list']:
            info.append( dict(task=myobject.task, modified=myobject.get_modified(), unixtime=format(myobject.modified, 'U'), todoid=myobject.id) )

        context['tags'] = Tag.objects.filter(todo__isnull=False).distinct('name')
        context['tagsearch'] = self.tagsearch
        context['cols'] = ['task', 'modified', 'unixtime', 'todoid']
        context['section'] = SECTION
        context['info'] = info
        return context


class BlobDetailView(UpdateView):
    template_name = 'blob/edit.html'
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super(BlobDetailView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['pk'] = self.kwargs.get('pk')
        context['metadata'] = self.object.metadata.all()
        context['action'] = 'Edit'
        return context

    def get(self, request, **kwargs):
        self.object = Blob.objects.get(user=self.request.user, id=self.kwargs.get('pk'))
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object, form=form)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        obj = Blob.objects.get(user=self.request.user, id=self.kwargs.get('pk'))
        return obj

    def form_valid(self, form):

        task = form.instance

        # Delete all existing tags
        task.tags.clear()

        # Then add the tags specified in the form
        for tag in form.cleaned_data['tags']:
            newtag, created = Tag.objects.get_or_create(name=tag.name)
            if created:
                newtag.save()
            task.tags.add(newtag)

        self.object = form.save()
        context = self.get_context_data(form=form)
        context["message"] = "Blob updated"
        return self.render_to_response(context)

    # def get_success_url(self):
    #     return reverse('todo_edit', kwargs={'pk': self.object.id})

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BlobDetailView, self).dispatch(*args, **kwargs)


