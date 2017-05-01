from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.templatetags.static import static
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormMixin, UpdateView
from django.views.generic.list import ListView

from collection.forms import CollectionForm
from collection.models import Collection
from blob.models import Blob
from tag.models import Tag

import datetime
import json
import os
from solrpy.core import SolrConnection

IMAGE_TYPE_LIST = ['jpeg', 'gif', 'png']
SECTION = 'Collections'


class CollectionListView(FormMixin, ListView):

    context_object_name = 'info'
    form_class = CollectionForm

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(CollectionListView, self).get_context_data(**kwargs)

        info = []

        for myobject in context['object_list']:
            info.append(dict(name=myobject.name, tags=myobject.get_tags(), created=myobject.get_created(), unixtime=format(myobject.created, 'U'), objectcount=len(myobject.blob_list) if myobject.blob_list else 0, id=myobject.id))

        context['cols'] = ['name', 'tags', 'created', 'unixtime', 'objectcount', 'id']
        context['section'] = SECTION
        context['info'] = info

        return context


class CollectionDetailView(DetailView):

    model = Collection
    slug_field = 'id'
    slug_url_kwarg = 'collection_id'

    def get_context_data(self, **kwargs):
        context = super(CollectionDetailView, self).get_context_data(**kwargs)

        if self.object.blob_list:
            q = 'id:(%s)' % ' '.join(['"blob_%s"' % t['id'] for t in self.object.blob_list])

            conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

            solr_args = {'q': q,
                         'rows': 1000,
                         'fields': ['attr_*', 'author', 'content_type', 'doctype', 'filepath', 'tags', 'title', 'author', 'url'],
                         'wt': 'json',
                         'fl': 'author,bordercore_todo_task,bordercore_bookmark_title,content_type,doctype,filepath,id,internal_id,attr_is_book,last_modified,tags,title,sha1sum,url,bordercore_blogpost_title'
            }

            results = conn.raw_query(**solr_args)

            # Build a temporary dict for fast lookup
            solr_list_objects = {}
            for x in json.loads(results.decode('UTF-8'))['response']['docs']:
                solr_list_objects[int(x['id'].split('blob_')[1])] = x

            # Solr doesn't return the blobs in the order specified in postgres, so we need to re-order
            blob_list_temp = []
            for blob in self.object.blob_list:
                try:
                    if blob.get('note', ''):
                        solr_list_objects[blob['id']]['note'] = blob['note']
                    blob_list_temp.append(solr_list_objects[blob['id']])
                except KeyError:
                    print("Warning: blob_id = %s not found in solr." % blob['id'])

            for object in blob_list_temp:
                if object['doctype'] in ('blob', 'book'):
                    filename = os.path.basename(object['filepath'])
                    object['url'] = object['filepath'].split(Blob.BLOB_STORE)[1]
                    object['cover_info'] = Blob.get_cover_info(object['sha1sum'], max_cover_image_width=70)
                    if object['content_type']:
                        try:
                            object['content_type'] = object['content_type'][0].split('/')[1]
                        except IndexError:
                            print("Warning: content_type malformed: id=%s, sha1sum=%s, content_type=%s" % (object['id'], object['sha1sum'], object['content_type']))
                        if object['content_type'] in IMAGE_TYPE_LIST:
                            object['is_image'] = True
                    if not object.get('title', ''):
                        object['title'] = filename

            context['blob_list'] = blob_list_temp
        return context


class CollectionCreateView(CreateView):
    template_name = 'collection/collection_list.html'
    form_class = CollectionForm

    def get_context_data(self, **kwargs):
        context = super(CollectionCreateView, self).get_context_data(**kwargs)
        context['action'] = 'Add'
        return context

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
        return reverse('collection_list')


class CollectionUpdateView(UpdateView):
    model = Collection
    form_class = CollectionForm
    success_url = reverse_lazy('collection_list')

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user

        # Delete all existing tags first
        obj.tags.clear()

        # Then add all tags specified
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)

        obj.save()

        return HttpResponseRedirect(self.get_success_url())


def get_info(request):

    from django.core.exceptions import ObjectDoesNotExist

    info = ''

    try:
        if request.GET.get('query_type', '') == 'id':
            match = Collection.objects.get(pk=request.GET['id'])
        else:
            match = Collection.objects.get(name=request.GET['name'])
        if match:
            info = {'name': match.name,
                    'description': match.description,
                    'id': match.id,
                    'tags': ','.join([tag.name for tag in match.tags.all()])}
    except ObjectDoesNotExist:
        pass

    return JsonResponse(info)


def sort_collection(request):

    collection_id = int(request.POST['collection_id'])
    blob_id = int(request.POST['blob_id'])
    new_position = int(request.POST['position'])

    collection = Collection.objects.get(user=request.user, id=collection_id)

    # First remove the blob from the existing list
    saved_blob = []
    new_blob_list = []

    for blob in collection.blob_list:
        if blob['id'] == blob_id:
            saved_blob = blob
        else:
            new_blob_list.append(blob)

    # Then re-insert it in its new position
    new_blob_list.insert(new_position - 1, saved_blob)
    collection.blob_list = new_blob_list

    collection.save()

    return JsonResponse('OK', safe=False)
