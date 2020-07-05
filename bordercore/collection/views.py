from pathlib import PurePath

from botocore.errorfactory import ClientError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, CharField, Value, When
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils.dateformat import format
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import (CreateView, DeleteView, FormMixin,
                                       UpdateView)
from django.views.generic.list import ListView

from blob.models import Blob
from collection.forms import CollectionForm
from collection.models import Collection

IMAGE_TYPE_LIST = ['jpeg', 'gif', 'png']
SECTION = 'kb'


@method_decorator(login_required, name='dispatch')
class CollectionListView(FormMixin, ListView):

    context_object_name = 'info'
    form_class = CollectionForm

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user).filter(is_private=False)

    def get_context_data(self, **kwargs):
        context = super(CollectionListView, self).get_context_data(**kwargs)

        info = []

        for myobject in context['object_list']:
            info.append(dict(name=myobject.name,
                             tags=myobject.get_tags(),
                             updated=myobject.get_modified(),
                             unixtime=format(myobject.modified, 'U'),
                             objectcount=len(myobject.blob_list) if myobject.blob_list else 0, id=myobject.id))

        context['cols'] = ['name', 'tags', 'updated', 'unixtime', 'objectcount', 'id']
        context['section'] = SECTION
        context['nav'] = 'collection'
        context['info'] = info
        context['title'] = 'Collection List'

        return context


@method_decorator(login_required, name='dispatch')
class CollectionDeleteView(DeleteView):

    def get_object(self, queryset=None):
        return Collection.objects.get(user=self.request.user, id=self.kwargs.get('pk'))

    def get_success_url(self):
        messages.add_message(self.request, messages.INFO, "Collection <strong>{}</strong> deleted".format(self.object.name))
        return reverse('collection_list')


@method_decorator(login_required, name='dispatch')
class CollectionDetailView(DetailView):

    model = Collection
    slug_field = 'id'
    slug_url_kwarg = 'collection_id'

    def get_context_data(self, **kwargs):
        context = super(CollectionDetailView, self).get_context_data(**kwargs)

        if self.kwargs.get('embedded', ''):
            self.template_name = 'collection/embedded.html'

        if self.object.blob_list:
            ids = [x['id'] for x in self.object.blob_list]
            order = Case(*[When(id=i, then=pos) for pos, i in enumerate(ids)])

            whens = [
                When(id=x['id'], then=Value(x.get('note', ''))) for x in self.object.blob_list
            ]

            blob_list = Blob.objects.filter(id__in=ids).annotate(
                collection_note=Case(
                    *whens,
                    output_field=CharField()
                )).order_by(order)

            for blob in blob_list:
                blob.cover_url = f"{PurePath(blob.get_s3_key()).parent}/cover.jpg"
                blob.title = blob.get_title(use_filename_if_present=True)

            context['blob_list'] = blob_list

            try:
                context['first_blob_cover_info'] = Blob.get_cover_info(user=self.request.user, sha1sum=blob_list.first().sha1sum)
            except ClientError:
                pass
        context['section'] = SECTION
        context['nav'] = 'collection'
        context['title'] = 'Collection Detail :: {}'.format(self.object.name)

        return context


@method_decorator(login_required, name='dispatch')
class CollectionCreateView(CreateView):
    template_name = 'collection/collection_list.html'
    form_class = CollectionForm

    def get_context_data(self, **kwargs):
        context = super(CollectionCreateView, self).get_context_data(**kwargs)
        context['action'] = 'Add'
        context['title'] = 'Add Collection'
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


@method_decorator(login_required, name='dispatch')
class CollectionUpdateView(UpdateView):
    model = Collection
    form_class = CollectionForm
    success_url = reverse_lazy('collection_list')

    def get_queryset(self):
        base_qs = super(CollectionUpdateView, self).get_queryset()
        return base_qs.filter(user=self.request.user)

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


@login_required
def get_info(request):

    from django.core.exceptions import ObjectDoesNotExist

    info = ''

    try:
        if request.GET.get('query_type', '') == 'id':
            match = Collection.objects.get(user=request.user, pk=request.GET['id'])
        else:
            match = Collection.objects.get(user=request.user, name=request.GET['name'])
        if match:
            info = {
                'name': match.name,
                'description': match.description,
                'id': match.id,
                'tags': [{"text": x.name, "is_meta": x.is_meta} for x in match.tags.all()]
            }
    except ObjectDoesNotExist:
        pass

    return JsonResponse(info)


@login_required
def sort_collection(request):

    collection_id = int(request.POST['collection_id'])
    blob_id = int(request.POST['blob_id'])
    new_position = int(request.POST['position'])

    collection = Collection.objects.get(user=request.user, id=collection_id)

    collection.sort(blob_id, new_position)

    return JsonResponse('OK', safe=False)


@login_required
def get_blob(request, collection_id, blob_position):

    collection = Collection.objects.get(pk=collection_id)

    return JsonResponse(collection.get_blob(blob_position))
