from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView

import hashlib
import json
import os

from blob.forms import BlobForm
from blob.models import MetaData
from tag.models import Tag
from blob.models import Blob

SECTION = 'Blob'
EBOOK_DIR = '/home/media/ebooks'
BLOB_STORE = '/home/media/blobs'

def blob_add(request):

    template_name = 'blob/add.html'
    message = ''

    if request.method == 'POST':

        hasher = hashlib.sha1()
        for chunk in request.FILES['blob'].chunks():
            hasher.update(chunk)

        # BLOCKSIZE = 65536
        # hasher = hashlib.sha1()
        # with open(filename, 'rb') as afile:
        #     buf = afile.read(BLOCKSIZE)
        #     while len(buf) > 0:
        #         hasher.update(buf)
        #         buf = afile.read(BLOCKSIZE)

        # Do we already know about this blob?
        existing_blob = Blob.objects.filter(sha1sum=hasher.hexdigest())
        if existing_blob:
            message = 'This blob already exists'
        else:
            if request.POST.get('store-on-filesystem', '') == 'on':
                filepath = store_blob(request.FILES['blob'], hasher.hexdigest(), store_as_ebook = True if request.POST.get('store-on-filesystem', '') == 'on' else False)
            else:
                filepath = "%s/%s" % (EBOOK_DIR, request.POST['filename'].split('\\')[-1])

            b = Blob(sha1sum = hasher.hexdigest(), file_path = filepath, user = request.user)
            b.save()
            return redirect('blob_edit', b.sha1sum)

    return render_to_response(template_name,
                              {'section': SECTION, 'message': message},
                              context_instance=RequestContext(request))


def store_blob(blob, sha1sum, store_as_ebook=False):

    if store_as_ebook:
        filepath = "%s/%s" % (EBOOK_DIR, blob.name)
    else:
        if not os.path.exists("%s/%s" % (BLOB_STORE, sha1sum[0:2])):
            os.makedirs("%s/%s/%s" % (BLOB_STORE, sha1sum[0:2], sha1sum))
        filepath = "%s/%s/%s/%s" % (BLOB_STORE, sha1sum[0:2], sha1sum, blob.name)
    with open(filepath, 'wb+') as destination:
        for chunk in blob.chunks():
            destination.write(chunk)

    return filepath


class BlobDetailView(UpdateView):
    template_name = 'blob/edit.html'
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super(BlobDetailView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['sha1sum'] = self.kwargs.get('sha1sum')
        context['metadata'] = self.object.metadata_set.all()
        context['action'] = 'Edit'
        return context

    def get(self, request, **kwargs):
        self.object = Blob.objects.get(user=self.request.user, sha1sum=self.kwargs.get('sha1sum'))
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object, form=form)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        obj = Blob.objects.get(user=self.request.user, sha1sum=self.kwargs.get('sha1sum'))
        return obj

    def form_valid(self, form):
        blob = form.instance

        # Delete all existing tags
        blob.tags.clear()

        if form.cleaned_data['replacement_sha1sum']:
            b = Blob.objects.get(sha1sum=form.cleaned_data['replacement_sha1sum'])
            tags = b.tags.all()
            form.cleaned_data['tags'] = tags

            # This block of code is needed to force the form to render the replacement tags
            data = form.data.copy()
            data['tags'] =  ", ".join([tag.name for tag in tags])
            form.data = data

            metadata = [[x.name, x.value] for x in b.metadata_set.all()]
        else:
            metadata = json.loads(self.request.POST['metadata'])

        # Metadata objects are not handled by the form -- handle them manually

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


