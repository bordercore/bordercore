from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from amazonproduct import API
from amazonproduct.errors import NoExactMatchesFound
import hashlib
import json
import os
import re
import shutil

from blob.forms import BlobForm
from blob.models import Blob, MetaData
from blob.tasks import index_document
from bookshelf.models import Bookshelf


SECTION = 'Blob'

amazon_api_config = {
}


def blob_add(request, replaced_sha1sum=None):

    template_name = 'blob/add.html'
    replaced_sha1sum_info = None

    if request.method == 'POST':

        hasher = hashlib.sha1()
        for chunk in request.FILES['blob'].chunks():
            hasher.update(chunk)

        # Do we already know about this blob?
        existing_blob = Blob.objects.filter(sha1sum=hasher.hexdigest())
        if existing_blob:
            messages.add_message(request, messages.INFO, 'This blob already exists.  <a href="%s">Click here to edit</a>' % reverse_lazy('blob_edit', kwargs={"sha1sum": existing_blob[0].sha1sum}), extra_tags='safe')
        else:
            store_blob(request.FILES['blob'], hasher.hexdigest())

            replaced_sha1sum = request.POST.get('replaced_sha1sum', '')
            if replaced_sha1sum != '':
                b = Blob.objects.get(sha1sum=replaced_sha1sum)
                old_tags = b.tags.all()
                old_metadata = b.metadata_set.all()
                b.sha1sum = hasher.hexdigest()
                b.pk = None
                b.save()
                b.filename = request.FILES['blob'].name
                b.file_path = "%s/%s" % (b.get_parent_dir(), b.filename)
                b.tags = old_tags
                b.metadata_set = old_metadata
                b.save()

                old_blob = Blob.objects.get(sha1sum=replaced_sha1sum)

                # Move any cover images from the old blob to the new
                for file in os.listdir(old_blob.get_parent_dir()):
                    filename, file_extension = os.path.splitext(file)
                    if file_extension[1:] in ['jpg', 'png']:
                        shutil.move("%s/%s" % (old_blob.get_parent_dir(), file), b.get_parent_dir())

                # Delete the old blob
                old_blob.delete()
            else:
                b = Blob(sha1sum=hasher.hexdigest(), filename=request.FILES['blob'].name, user=request.user)
                b.save()

            return redirect('blob_edit', b.sha1sum)

    else:

        try:
            replaced_sha1sum_info = Blob.objects.get(sha1sum=replaced_sha1sum)
            replaced_sha1sum_info.metadata = [[x.name, x.value] for x in replaced_sha1sum_info.metadata_set.all()]
        except ObjectDoesNotExist:
            replaced_sha1sum_info = None

    return render_to_response(template_name,
                              {'replaced_sha1sum_info': replaced_sha1sum_info, 'section': SECTION},
                              context_instance=RequestContext(request))


def store_blob(blob, sha1sum):

    if not os.path.exists("%s/%s/%s" % (Blob.BLOB_STORE, sha1sum[0:2], sha1sum)):
        os.makedirs("%s/%s/%s" % (Blob.BLOB_STORE, sha1sum[0:2], sha1sum))
    filepath = "%s/%s/%s/%s" % (Blob.BLOB_STORE, sha1sum[0:2], sha1sum, blob.name)

    with open(filepath, 'wb+') as destination:
        for chunk in blob.chunks():
            destination.write(chunk)

    return filepath


class BlobDeleteView(DeleteView):
    model = Blob
    success_url = reverse_lazy('blob_add')

    def post(self, request, *args, **kwargs):
        obj = super(BlobDeleteView, self).post(request, *args, **kwargs)
        messages.add_message(request, messages.INFO, 'Blob deleted')
        return obj


class BlobDetailView(DetailView):

    model = Blob
    slug_field = 'sha1sum'
    slug_url_kwarg = 'sha1sum'

    def get_context_data(self, **kwargs):
        context = super(BlobDetailView, self).get_context_data(**kwargs)
        context['id'] = self.object.id
        context['metadata'] = {}
        for x in self.object.metadata_set.all():
            if context['metadata'].get(x.name, ''):
                context['metadata'][x.name] = ', '.join([context['metadata'][x.name], x.value])
            else:
                context['metadata'][x.name] = x.value
        context['cover_url'] = self.object.get_cover_url('large')
        context['cover_url_small'] = self.object.get_cover_url('small')
        try:
            query = 'sha1sum:%s' % self.object.sha1sum
            context['solr_info'] = self.object.get_solr_info(query)['docs'][0]
            context['content_type'] = self.object.get_content_type(context['solr_info']['content_type'][0])
        except IndexError, e:
            context['error'] = 'Error retrieving info from Solr'
            print ("%s, sha1sum=%s, error=%s" % (context['error'], self.object.sha1sum, e))
        context['title'] = self.object.get_title(remove_edition_string=True)

        try:
            all_shelves = Bookshelf.objects.filter(user=self.request.user).order_by('name')
            current_shelves = {}
            context['all_shelves'] = [{'id': x.id, 'name': x.name} for x in all_shelves]
            for shelf in all_shelves:
                if shelf.blob_list and self.object.id in shelf.blob_list:
                    current_shelves[shelf.id] = True
            context['current_shelves'] = current_shelves
        except KeyError:
            pass

        return context


class BlobUpdateView(UpdateView):
    template_name = 'blob/edit.html'
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super(BlobUpdateView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['sha1sum'] = self.kwargs.get('sha1sum')
        context['metadata'] = [x for x in self.object.metadata_set.all() if x.name != 'is_book']
        cover_url = self.object.get_cover_url('large')
        if cover_url:
            context['cover_url'] = 'blobs/' + cover_url
        else:
            context['cover_url'] = 'img/no_image_available.svg'
        if True in [True for x in self.object.metadata_set.all() if x.name == 'is_book']:
            context['is_book'] = True
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

        metadata = json.loads(self.request.POST['metadata'])

        # Metadata objects are not handled by the form -- handle them manually

        # Delete all existing metadata
        blob.metadata_set.all().delete()

        for m in metadata:
            new_metadata, created = MetaData.objects.get_or_create(name=m[0], value=m[1], blob=blob)
            if created:
                new_metadata.save()
        if self.request.POST.get('is_book', ''):
            new_metadata = MetaData(name='is_book', value='true', blob=blob)
            new_metadata.save()

        self.object = form.save()
        context = self.get_context_data(form=form)
        messages.add_message(self.request, messages.INFO, 'Blob updated')

        index_document.delay(blob.sha1sum)

        return self.render_to_response(context)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BlobUpdateView, self).dispatch(*args, **kwargs)


def metadata_name_search(request):

    m = MetaData.objects.all().values('name').filter(name__icontains=request.GET['query']).distinct('name').order_by('name'.lower())

    return_data = [{'value': x['name']} for x in m]

    return render_to_response('return_json.json',
                              {'info': json.dumps(return_data)},
                              content_type="application/json",
                              context_instance=RequestContext(request))


def get_amazon_image_info(request, sha1sum, index=0):

    b = Blob.objects.get(sha1sum=sha1sum)
    result = b.get_amazon_cover_url(int(index))

    return render_to_response('return_json.json',
                              {'info': json.dumps(result)},
                              content_type="application/json",
                              context_instance=RequestContext(request))


def set_amazon_image_info(request, sha1sum, index=0):

    b = Blob.objects.get(sha1sum=sha1sum)
    try:
        b.set_amazon_cover_url('small', request.POST['small'])
        b.set_amazon_cover_url('medium', request.POST['medium'])
        b.set_amazon_cover_url('large', request.POST['large'])
        result = {'message': 'Cover image updated'}
    except Exception, e:
        result = {'message': str(e), 'error': True}

    return render_to_response('return_json.json',
                              {'info': json.dumps(result)},
                              content_type="application/json",
                              context_instance=RequestContext(request))


def get_amazon_metadata(request, title):

    api = API(cfg=amazon_api_config)

    return_data = {'data': []}

    try:
        results = api.item_search('Books', Title=title, ResponseGroup='Medium', Sort='-publication_date')
        for result in results:
            try:
                return_data['data'].append(['Title', result.ItemAttributes.Title.text])
                author_raw = result.ItemAttributes.Author.text
                matches = re.split("\s?;\s?|\s?,\s?", author_raw)
                for author in matches:
                    return_data['data'].append(['Author', author.strip()])
                publication_data_raw = str(result.ItemAttributes.PublicationDate)
                matches = re.match(r'^(\d\d\d\d)', publication_data_raw)
                if matches:
                    return_data['data'].append(['Publication Date', matches.group(1)])
                else:
                    return_data['data'].append(['Publication Date', str(result.ItemAttributes.PublicationDate)])
            except AttributeError, e:
                print "AttributeError: %s" % e
    except NoExactMatchesFound:
        return_data['error'] = "No Amazon matches found"

    return render_to_response('return_json.json',
                              {'info': json.dumps(return_data)},
                              content_type="application/json",
                              context_instance=RequestContext(request))


# Temp code to randomly choose blobs with insufficient metadata to edit
def blob_todo(request):

    import solr
    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

    solr_args = {'wt': 'json',
                 'fl': 'id,sha1sum,filepath,tags,internal_id',
                 'q': 'doctype:book AND -tags:[* TO *]',
                 'rows': 500}

    results = json.loads(conn.raw_query(**solr_args))

    import random
    blob = random.choice(results['response']['docs'])
    print blob['sha1sum']

    return redirect('blob_edit', blob['sha1sum'])
