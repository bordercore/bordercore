from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView
import json

from blob.forms import BlobForm
from blob.models import MetaData
from tag.models import Tag
from blob.models import Blob

SECTION = 'Blob'


class BlobDetailView(UpdateView):
    template_name = 'blob/edit.html'
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super(BlobDetailView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['pk'] = self.kwargs.get('pk')
        context['metadata'] = self.object.metadata_set.all()
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

        blob = form.instance

        # Delete all existing tags
        blob.tags.clear()

        # Then add the tags specified in the form
        for tag in form.cleaned_data['tags']:
            newtag, created = Tag.objects.get_or_create(name=tag.name)
            if created:
                newtag.save()
            blob.tags.add(newtag)

        # Metadata objects are not handled by the form -- handle them manually
        metadata = json.loads(self.request.POST['metadata'])

        # Delete all existing metadata
        blob.metadata_set.all().delete()

        for m in metadata:
            new_metadata, created = MetaData.objects.get_or_create(name=m[0], value=m[1], blob=blob)
            if created:
                new_metadata.save()

        self.object = form.save()
        context = self.get_context_data(form=form)
        context["message"] = "Blob updated"
        return self.render_to_response(context)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BlobDetailView, self).dispatch(*args, **kwargs)


def metadata_name_search(request):

    m = MetaData.objects.all().values('name').filter(name__icontains=request.GET['query']).distinct('name').order_by('name'.lower())

    return_data = [{'value': x['name']} for x in m]

    return render_to_response('return_json.json',
                              { 'info': json.dumps(return_data) },
                              content_type="application/json",
                              context_instance=RequestContext(request))


