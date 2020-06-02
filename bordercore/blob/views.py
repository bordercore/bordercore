import datetime
import logging
import random
import re

import boto3
import humanize
from amazonproduct import API
from amazonproduct.errors import NoExactMatchesFound
from botocore.errorfactory import ClientError
from PyPDF2.utils import PdfReadError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from blob.forms import BlobForm
from blob.models import Blob, MetaData
from collection.models import Collection
from lib.time_utils import parse_date_from_string

SECTION = 'kb'

# TODO: Move this to Django config file
amazon_api_config = {
}

log = logging.getLogger(f"bordercore.{__name__}")


@method_decorator(login_required, name='dispatch')
class BlobCreateView(CreateView):
    template_name = 'blob/edit.html'
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super(BlobCreateView, self).get_context_data(**kwargs)
        context['action'] = 'Add'
        if self.request.GET.get('linked_blob', ''):
            linked_blob = Blob.objects.get(user=self.request.user, id=self.request.GET['linked_blob'])
            context['linked_blob'] = linked_blob
            # Grab the initial metadata from the linked blob
            context['metadata'] = linked_blob.metadata_set.all()
        if self.request.GET.get('linked_collection', ''):
            collection_id = self.request.GET['linked_collection']
            context['linked_collection_info'] = Collection.objects.get(user=self.request.user, id=collection_id)
            context['linked_collection_blob_list'] = [Blob.objects.get(user=self.request.user, pk=x['id']) for x in Collection.objects.get(user=self.request.user, id=collection_id).blob_list]
            # Grab the initial metadata from one of the other blobs in the collection
            context['metadata'] = context['linked_collection_blob_list'][0].metadata_set.all()
        context['section'] = SECTION
        context['nav'] = 'blob'
        context['title'] = 'Add Blob'
        return context

    def get_form(self, form_class=None):
        form = super(BlobCreateView, self).get_form(form_class)

        if self.request.GET.get('is_note', False):
            form.initial['is_note'] = True
        if self.request.GET.get('linked_blob', False):
            blob = Blob.objects.get(user=self.request.user, pk=int(self.request.GET.get('linked_blob')))
            form.initial['tags'] = ','.join([x.name for x in blob.tags.all()])
            form.initial['date'] = blob.date
            form.initial['title'] = blob.title
        if self.request.GET.get('linked_collection', False):
            collection_id = self.request.GET['linked_collection']
            blob_id = Collection.objects.get(user=self.request.user, id=collection_id).blob_list[0]['id']
            blob = Blob.objects.get(user=self.request.user, pk=blob_id)
            form.initial['tags'] = ','.join([x.name for x in blob.tags.all()])
            form.initial['date'] = blob.date
            form.initial['title'] = blob.title

        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.file_modified = form.cleaned_data['file_modified']
        obj.save()

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data['tags']:
            obj.tags.add(tag)

        obj.save()

        handle_metadata(obj, self.request)

        handle_linked_blob(obj, self.request)

        handle_linked_collection(obj, self.request)

        obj.index_blob()

        return super(BlobCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blob_detail', kwargs={'uuid': self.object.uuid})


@method_decorator(login_required, name='dispatch')
class BlobDeleteView(DeleteView):
    model = Blob
    success_url = reverse_lazy('blob_add')

    # Override delete() so that we can catch any exceptions, especially any
    #  thrown by Elasticsearch
    def delete(self, request, *args, **kwargs):
        try:
            return super(BlobDeleteView, self).delete(request, *args, **kwargs)
        except Exception as e:
            messages.add_message(request, messages.ERROR, f"Error deleting object: {e}")
            return HttpResponseRedirect(reverse('blob_edit', kwargs={'uuid': str(self.get_object().uuid)}))

    def get_object(self, queryset=None):
        obj = Blob.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        return obj


@method_decorator(login_required, name='dispatch')
class BlobDetailView(DetailView):

    model = Blob
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    # When we rename the object, we should be able to remove this and let
    # Django figure out the template name on its own
    template_name = 'blob/blob_detail.html'

    def get_context_data(self, **kwargs):
        context = super(BlobDetailView, self).get_context_data(**kwargs)
        context['id'] = self.object.id
        context['metadata'] = self.object.get_metadata()
        context['urls'] = self.object.get_urls()

        from lib.time_utils import get_date_from_pattern
        context['date'] = get_date_from_pattern({"gte": self.object.date})

        if self.object.sha1sum:
            context["aws_url"] = f"https://s3.console.aws.amazon.com/s3/buckets/{settings.AWS_STORAGE_BUCKET_NAME}/blobs/{self.object.sha1sum[:2]}/{self.object.sha1sum}/"
            try:
                context['cover_info'] = Blob.get_cover_info(self.request.user, self.object.sha1sum)
            except ClientError:
                log.warn(f"No S3 cover image found for id={self.object.id}")
        if self.object.is_note:
            context["is_favorite_note"] = self.object.is_favorite_note()
        try:
            context["elasticsearch_info"] = self.object.get_elasticsearch_info()
            if self.object.sha1sum and context["elasticsearch_info"].get("size"):
                context["size"] = humanize.naturalsize(context["elasticsearch_info"]["size"])
            if context["elasticsearch_info"].get("content_type", None):
                context["content_type"] = Blob.get_content_type(context["elasticsearch_info"]["content_type"])
        except IndexError:
            # Give Solr up to a minute to index the blob
            if int(datetime.datetime.now().strftime("%s")) - int(self.object.created.strftime("%s")) < 60:
                messages.add_message(self.request, messages.INFO, 'New blob not yet indexed in Elasticsearch')
            else:
                messages.add_message(self.request, messages.ERROR, 'Blob not found in Elasticsearch')
        context['caption'] = self.object.get_title(remove_edition_string=True)
        context['fields_ignore'] = ['is_book', 'Url', 'Publication Date', 'Title', 'Author']

        context['current_collections'] = Collection.objects.filter(user=self.request.user, blob_list__contains=[{'id': self.object.id}])

        collection_info = []
        linked_blobs = []

        for collection in Collection.objects.filter(user=self.request.user, blob_list__contains=[{'id': self.object.id}]):
            blob_list = Blob.objects.filter(user=self.request.user, pk__in=[x['id'] for x in collection.blob_list if x['id'] != self.object.id])
            if collection.is_private:
                linked_blobs.append({'id': collection.id,
                                     'name': collection.name,
                                     'is_private': collection.is_private,
                                     'blob_list': blob_list})
            else:
                collection_info.append({'id': collection.id,
                                        'name': collection.name})
        context['collection_info'] = collection_info
        context['linked_blobs'] = linked_blobs
        if self.object.is_note:
            context["section"] = "notes"
        else:
            context['section'] = SECTION
        return context

    def get_queryset(self):
        return Blob.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class BlobUpdateView(UpdateView):
    template_name = 'blob/edit.html'
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super(BlobUpdateView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['sha1sum'] = self.kwargs.get('sha1sum')

        try:
            context['cover_info'] = Blob.get_cover_info(self.request.user, self.object.sha1sum, max_cover_image_width=400)
        except ClientError:
            log.warn(f"No S3 cover image found for id={self.object.id}")

        context['metadata'] = self.object.metadata_set.all()
        if True in [True for x in self.object.metadata_set.all() if x.name == 'is_book']:
            context['is_book'] = True
        context['is_private'] = self.object.is_private
        context['is_note'] = self.object.is_note
        context['collections_other'] = Collection.objects.filter(Q(user=self.request.user)
                                                                 & ~Q(blob_list__contains=[{'id': self.object.id}])
                                                                 & Q(is_private=False))
        context['action'] = 'Edit'
        context['title'] = 'Blob Edit :: {}'.format(self.object.get_title(remove_edition_string=True))
        return context

    def get(self, request, **kwargs):
        self.object = Blob.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object, form=form)
        return render(request, self.template_name, context)

    def get_object(self, queryset=None):
        obj = Blob.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        return obj

    def form_valid(self, form):
        blob = form.instance

        file_changed = False if 'file' not in form.changed_data else True

        # Only check for a renamed file if the file itself hasn't changed
        if not file_changed:
            old_filename = str(form.instance.file)
            new_filename = form.cleaned_data['filename']

            if (new_filename != old_filename):

                try:
                    key_root = f"{settings.MEDIA_ROOT}/{blob.sha1sum[0:2]}/{blob.sha1sum}"
                    s3 = boto3.resource("s3")
                    s3.Object(settings.AWS_STORAGE_BUCKET_NAME, f"{key_root}/{new_filename}").copy_from(CopySource=f"{settings.AWS_STORAGE_BUCKET_NAME}/{key_root}/{old_filename}")
                    s3.Object(settings.AWS_STORAGE_BUCKET_NAME, f"{key_root}/{old_filename}").delete()

                    blob.file = new_filename
                    blob.file_modified = None
                    blob.save()
                except Exception as e:
                    from django.forms import ValidationError
                    raise ValidationError("Error: {}".format(e))

        blob.file_modified = form.cleaned_data['file_modified']

        # Delete all existing tags
        blob.tags.clear()

        handle_metadata(blob, self.request)

        self.object = form.save()

        self.object.index_blob(file_changed)

        messages.add_message(self.request, messages.INFO, 'Blob updated')

        return HttpResponseRedirect(reverse('blob_detail', kwargs={'uuid': str(blob.uuid)}))


@method_decorator(login_required, name='dispatch')
class BlobThumbnailView(UpdateView):
    template_name = 'blob/thumbnail.html'
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super(BlobThumbnailView, self).get_context_data(**kwargs)
        context['cover_info'] = Blob.get_cover_info(self.request.user, self.object.sha1sum, max_cover_image_width=70, size='small')
        context['filename'] = self.object.file
        query = 'uuid:{}'.format(self.object.uuid)
        # context['solr_info'] = self.object.get_solr_info(query)['docs'][0]
        # if context['solr_info'].get('content_type', ''):
        #     context['content_type'] = Blob.get_content_type(context['solr_info']['content_type'][0]).lower()
        context['section'] = SECTION
        context['title'] = 'Blob Thumbnail :: {}'.format(self.object.get_title(remove_edition_string=True))

        return context

    def get_object(self, queryset=None):
        obj = Blob.objects.get(user=self.request.user, uuid=self.kwargs.get('uuid'))
        return obj


# Metadata objects are not handled by the form -- handle them manually
def handle_metadata(blob, request):

    metadata_old = blob.metadata_set.all()
    for i in metadata_old:
        i.delete()

    for key, value in request.POST.items():
        p = re.compile(r"^\d+_(.*)")
        m = p.match(key)
        if m:
            new_metadata, created = MetaData.objects.get_or_create(user=request.user, name=m.group(1), value=value.strip(), blob=blob)
            if created:
                new_metadata.save()

    if request.POST.get('is_book', ''):
        new_metadata = MetaData(user=request.user, name='is_book', value='true', blob=blob)
        new_metadata.save()


def handle_linked_blob(blob, request):

    if request.POST.get('linked_blob', ''):
        blob_list = [{'id': int(request.POST['linked_blob']), 'added': int(datetime.datetime.now().strftime("%s"))},
                     {'id': blob.id, 'added': int(datetime.datetime.now().strftime("%s"))}]
        collection = Collection(blob_list=blob_list, user=request.user, is_private=True)
        collection.save()


def handle_linked_collection(blob, request):

    if request.POST.get('linked_collection', ''):
        collection = Collection.objects.get(user=request.user, id=int(request.POST['linked_collection']))
        blob = {'id': blob.id, 'added': int(datetime.datetime.now().strftime("%s"))}
        collection.blob_list.append(blob)
        collection.save()


@login_required
def metadata_name_search(request):

    m = MetaData.objects.filter(user=request.user).values('name').filter(name__icontains=request.GET['query']).distinct('name').order_by('name'.lower())

    return_data = [{'value': x['name']} for x in m]

    return JsonResponse(return_data, safe=False)


@login_required
def get_amazon_image_info(request, sha1sum, index=0):

    b = Blob.objects.get(user=request.user, sha1sum=sha1sum)
    result = b.get_amazon_cover_url(index)

    return JsonResponse(result)


@login_required
def set_amazon_image_info(request, sha1sum, index=0):

    b = Blob.objects.get(user=request.user, sha1sum=sha1sum)
    try:
        b.set_amazon_cover_url('small', request.POST['small'])
        b.set_amazon_cover_url('large', request.POST['large'])
        result = {'message': 'Cover image updated'}
    except Exception as e:
        result = {'message': str(e), 'error': True}

    return JsonResponse(result)


def amazon_metadata_dupe_check(dupes, name, value):
    if value in dupes[name]:
        return False
    else:
        dupes[name][value] = True
        return True


@login_required
def slideshow(request):
    """
    Select a random blob from the collection "To Display"
    to display in a slideshow
    """

    c = Collection.objects.filter(name="To Display")[0]

    blob = Blob.objects.get(pk=random.choice(c.blob_list)["id"])

    content_type = None
    try:
        content_type = Blob.get_content_type(blob.get_elasticsearch_info()["content_type"])
    except Exception:
        log.warning(f"Can't get content type for uuid={blob.uuid}")

    return render(request, "blob/slideshow.html",
                  {"section": SECTION,
                   "content_type": content_type,
                   "blob": blob})

@login_required
def get_amazon_metadata(request, title):

    api = API(cfg=amazon_api_config)

    return_data = {'data': []}
    dupes = {'Title': {}, 'Author': {}, 'Publication Date': {}}

    try:
        results = api.item_search('Books', Title=title, ResponseGroup='Medium', Sort='-publication_date')
        for result in results:
            try:
                title = result.ItemAttributes.Title.text
                if amazon_metadata_dupe_check(dupes, 'Title', title):
                    return_data['data'].append(['Title', title])
                author_raw = result.ItemAttributes.Author.text
                matches = [x.strip() for x in re.split(r"\s?;\s?|\s?,\s?", author_raw)]
                for author in matches:
                    if amazon_metadata_dupe_check(dupes, 'Author', author):
                        return_data['data'].append(['Author', author])
                publication_data_raw = str(result.ItemAttributes.PublicationDate)
                matches = re.match(r'^(\d\d\d\d)', publication_data_raw)
                if matches:
                    publication_date = matches.group(1)
                else:
                    publication_date = str(result.ItemAttributes.PublicationDate)
                if amazon_metadata_dupe_check(dupes, 'Publication Date', publication_date):
                    return_data['data'].append(['Publication Date', publication_date])
            except AttributeError as e:
                log.error("AttributeError: %s" % e)
    except NoExactMatchesFound:
        return_data['error'] = "No Amazon matches found"

    return JsonResponse(return_data)


@login_required
def create_thumbnail(request, uuid, page_number=None):
    b = Blob.objects.get(user=request.user, uuid=uuid)

    try:
        b.create_thumbnail(page_number)
    except PdfReadError as e:
        return JsonResponse({'error': str(e)})

    cover_info = Blob.get_cover_info(request.user,
                                            b.sha1sum,
                                            max_cover_image_width=70,
                                            size='small')

    return JsonResponse({'message': 'OK', 'cover_url': cover_info['url']})


@login_required
def collection_mutate(request):

    blob_id = int(request.POST['blob_id'])
    collection = Collection.objects.get(user=request.user, id=int(request.POST['collection_id']))
    mutation = request.POST['mutation']

    message = ''

    if mutation == 'add':
        blob = {'id': blob_id, 'added': int(datetime.datetime.now().strftime("%s"))}
        if collection.blob_list:
            if [x for x in collection.blob_list if x['id'] == blob_id]:
                message = 'Blob already in collection'
            else:
                collection.blob_list.insert(0, blob)
        else:
            collection.blob_list = [blob]
        message = 'Added to collection'
    elif mutation == 'delete':
        collection.blob_list = [x for x in collection.blob_list if x['id'] != blob_id]
        message = 'Deleted from collection'

    collection.save()

    return JsonResponse({'message': message})


@login_required
def parse_date(request, input_date):

    error = None
    response = ""

    try:
        response = parse_date_from_string(input_date)
    except ValueError as e:
        error = str(e)

    return JsonResponse({'output_date': response,
                         'error': error})
