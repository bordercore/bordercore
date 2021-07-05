import datetime
import json
import logging
import random
import re

import boto3
from botocore.errorfactory import ClientError

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
from django.views.generic.list import ListView

from blob.forms import BlobForm
from blob.models import Blob, MetaData
from blob.services import get_recent_blobs
from collection.models import Collection
from lib.time_utils import parse_date_from_string

log = logging.getLogger(f"bordercore.{__name__}")


@method_decorator(login_required, name="dispatch")
class BlobListView(ListView):

    def get_queryset(self):
        return Blob.objects.filter(user=self.request.user). \
            prefetch_related("tags"). \
            order_by("-created")[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return {
            **context,
            "title": "Recent Blobs"
        }


@method_decorator(login_required, name='dispatch')
class BlobCreateView(CreateView):
    template_name = 'blob/update.html'
    form_class = BlobForm

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in QuestionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        if self.request.GET.get('linked_blob', ''):
            linked_blob = Blob.objects.get(user=self.request.user, id=self.request.GET['linked_blob'])
            context['linked_blob'] = linked_blob
            # Grab the initial metadata from the linked blob
            context['metadata'] = linked_blob.metadata_set.all()
        if 'linked_collection' in self.request.GET:
            collection_uuid = self.request.GET['linked_collection']
            context['linked_collection_info'] = Collection.objects.get(user=self.request.user, uuid=collection_uuid)
            context['linked_collection_blob_list'] = [Blob.objects.get(user=self.request.user, pk=x['id']) for x in Collection.objects.get(user=self.request.user, uuid=collection_uuid).blob_list]
            # Grab the initial metadata from one of the other blobs in the collection
            context['metadata'] = context['linked_collection_blob_list'][0].metadata_set.all()
        collection_id = self.request.GET.get('collection_id', '')
        if collection_id:
            context['collection_info'] = Collection.objects.get(user=self.request.user, id=collection_id)
        context['title'] = 'Create Blob'

        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.request.GET.get('is_note', False):
            form.initial['is_note'] = True
        if self.request.GET.get('linked_blob', False):
            blob = Blob.objects.get(user=self.request.user, pk=int(self.request.GET.get('linked_blob')))
            form.initial['tags'] = ','.join([x.name for x in blob.tags.all()])
            form.initial['date'] = blob.date
            form.initial['name'] = blob.name
        if self.request.GET.get('linked_collection', False):
            collection_uuid = self.request.GET['linked_collection']
            blob_id = Collection.objects.get(user=self.request.user, uuid=collection_uuid).blob_list[0]['id']
            blob = Blob.objects.get(user=self.request.user, pk=blob_id)
            form.initial['tags'] = ','.join([x.name for x in blob.tags.all()])
            form.initial['date'] = blob.date
            form.initial['name'] = blob.name

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

        handle_add_collection(obj, self.request)

        obj.index_blob()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blob:detail', kwargs={'uuid': self.object.uuid})


@method_decorator(login_required, name="dispatch")
class BlobDeleteView(DeleteView):
    model = Blob
    success_url = reverse_lazy("blob:list")

    # Override delete() so that we can catch any exceptions, especially any
    #  thrown by Elasticsearch
    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.add_message(self.request, messages.INFO, "Blob successfully deleted")
            return response
        except Exception as e:
            messages.add_message(request, messages.ERROR, f"Error deleting object: {e}")
            return HttpResponseRedirect(reverse("blob:update", kwargs={"uuid": str(self.get_object().uuid)}))

    def get_object(self, queryset=None):
        obj = Blob.objects.get(user=self.request.user, uuid=self.kwargs.get("uuid"))
        return obj


@method_decorator(login_required, name="dispatch")
class BlobDetailView(DetailView):

    model = Blob
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["metadata"], context["urls"] = self.object.get_metadata()

        context["metadata_misc"] = {
            key: value for (key, value)
            in context["metadata"].items()
            if key not in [
                "is_book",
                "Url",
                "Publication Date",
                "Subtitle",
                "Name",
                "Author"
            ]
        }

        context["date"] = self.object.get_date()

        context["cover_info"] = {}
        if self.object.sha1sum:
            context["aws_url"] = f"https://s3.console.aws.amazon.com/s3/buckets/{settings.AWS_STORAGE_BUCKET_NAME}/blobs/{self.object.uuid}/"
            try:
                context["cover_info"] = self.object.get_cover_info()
            except ClientError:
                log.warn(f"No S3 cover image found for id={self.object.id}")

        if self.object.is_note:
            context["is_pinned_note"] = self.object.is_pinned_note()

        try:
            context["elasticsearch_info"] = self.object.get_elasticsearch_info()
        except IndexError:
            if int(datetime.datetime.now().strftime("%s")) - int(self.object.created.strftime("%s")) < 60:
                # Give Elasticsearch up to a minute to index the blob
                messages.add_message(self.request, messages.INFO, "New blob not yet indexed in Elasticsearch")
            else:
                messages.add_message(self.request, messages.ERROR, "Blob not found in Elasticsearch")

        context["caption"] = self.object.get_name(remove_edition_string=True)

        context["linked_blobs"] = self.object.get_linked_blobs()

        context["collection_list"] = self.object.get_collection_info()

        if "content_type" in context or self.object.sha1sum or context["metadata_misc"]:
            context["show_metadata"] = True
        else:
            context["show_metadata"] = False

        context["tree"] = json.dumps(
            {
                "label": "Root",
                "nodes": self.object.get_tree()
            }
        )

        return context

    def get_queryset(self):
        return Blob.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class BlobUpdateView(UpdateView):
    template_name = 'blob/update.html'
    form_class = BlobForm

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in BlobForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sha1sum'] = self.kwargs.get('sha1sum')

        try:
            context['cover_info'] = self.object.get_cover_info(max_cover_image_width=400)
        except ClientError:
            log.warn(f"No S3 cover image found for id={self.object.id}")

        context['metadata'] = self.object.metadata_set.exclude(name="is_book")

        if [x for x in self.object.metadata_set.all() if x.name == 'is_book']:
            context['is_book'] = True

        context['is_private'] = self.object.is_private
        context['is_note'] = self.object.is_note
        context['collections_other'] = Collection.objects.filter(Q(user=self.request.user)
                                                                 & ~Q(blob_list__contains=[{'id': self.object.id}])
                                                                 & Q(is_private=False))
        context['action'] = 'Update'
        context['title'] = 'Blob Update :: {}'.format(self.object.get_name(remove_edition_string=True))
        context['tags'] = [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
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
                    key_root = f"{settings.MEDIA_ROOT}/{blob.uuid}"
                    s3 = boto3.resource("s3")
                    s3.Object(
                        settings.AWS_STORAGE_BUCKET_NAME, f"{key_root}/{new_filename}"
                    ).copy_from(
                        CopySource=f"{settings.AWS_STORAGE_BUCKET_NAME}/{key_root}/{old_filename}"
                    )
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

        return HttpResponseRedirect(reverse('blob:detail', kwargs={'uuid': str(blob.uuid)}))


@method_decorator(login_required, name="dispatch")
class BlobCoverInfoView(DetailView):

    model = Blob
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get(self, request, *args, **kwargs):

        try:
            cover_info = self.get_object().get_cover_info()
        except ClientError:
            cover_info = {}
        return JsonResponse(cover_info, safe=False)

    def get_queryset(self):
        return Blob.objects.filter(user=self.request.user)


# Metadata objects are not handled by the form -- handle them manually
def handle_metadata(blob, request):

    metadata_old = blob.metadata_set.all()
    for i in metadata_old:
        i.delete()

    for key, value in request.POST.items():
        p = re.compile(r"^\d+_(.*)")
        m = p.match(key)
        if m:
            name = m.group(1)
            if name == "" or value.strip() == "":
                continue
            new_metadata, created = MetaData.objects.get_or_create(user=request.user, name=name, value=value.strip(), blob=blob)
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
        collection = Collection.objects.get(user=request.user, uuid=request.POST['linked_collection'])
        blob = {'id': blob.id, 'added': int(datetime.datetime.now().strftime("%s"))}
        collection.blob_list.append(blob)
        collection.save()


def handle_add_collection(blob, request):

    if request.POST.get('collection_id', ''):
        collection = Collection.objects.get(user=request.user, id=int(request.POST['collection_id']))
        blob = {'id': blob.id, 'added': int(datetime.datetime.now().strftime("%s"))}
        if collection.blob_list:
            collection.blob_list.append(blob)
        else:
            collection.blob_list = [blob]
        collection.save()


@login_required
def metadata_name_search(request):

    m = MetaData.objects.filter(user=request.user).values('name').filter(name__icontains=request.GET['query']).distinct('name').order_by('name'.lower())

    return_data = [{'value': x['name']} for x in m]

    return JsonResponse(return_data, safe=False)


@login_required
def slideshow(request):
    """
    Select a random blob from the collection "To Display"
    to display in a slideshow
    """

    c = Collection.objects.filter(name="To Display").first()

    blob = Blob.objects.get(pk=random.choice(c.blob_list)["id"])

    content_type = None
    try:
        content_type = blob.get_elasticsearch_info()["content_type"]
    except Exception:
        log.warning(f"Can't get content type for uuid={blob.uuid}")

    return render(request, "blob/slideshow.html",
                  {"content_type": content_type,
                   "blob": blob})


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
        message = f"Added to collection '{collection.name}'"
    elif mutation == 'delete':
        collection.blob_list = [x for x in collection.blob_list if x['id'] != blob_id]
        message = f"Removed from collection '{collection.name}'"

    collection.save()

    return JsonResponse({"status": "OK", "message": message}, safe=False)


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


@login_required
def recent_blobs(request):

    blob_list, doctypes = get_recent_blobs(request.user)

    response = {
        "blobList": blob_list,
        "docTypes": doctypes,
        "status": "OK"
    }

    return JsonResponse(response, safe=False)
