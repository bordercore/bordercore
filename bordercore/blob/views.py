import datetime
import json
import logging
import re

import boto3

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from blob.forms import BlobForm
from blob.models import Blob, MetaData, RecentlyViewedBlob
from blob.services import get_recent_blobs, import_blob
from collection.models import Collection, SortOrderCollectionBlob
from lib.mixins import FormRequestMixin
from lib.time_utils import get_javascript_date, parse_date_from_string

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


@method_decorator(login_required, name="dispatch")
class BlobCreateView(FormRequestMixin, CreateView):
    template_name = "blob/update.html"
    form_class = BlobForm

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""

        # Add 'T00:00' to force JavaScript to use localtime
        form["date"].value = get_javascript_date(form["date"].value()) + "T00:00"

        if form["importance"].value():
            form["importance"].value = 10

        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"

        if "linked_blob_uuid" in self.request.GET:
            linked_blob = Blob.objects.get(user=self.request.user, uuid=self.request.GET["linked_blob_uuid"])
            context["linked_blob"] = linked_blob
            context["linked_blob"].thumbnail_url = linked_blob.get_cover_url_small()

            # Grab the initial metadata and tags from the linked blob
            context["metadata"] = linked_blob.metadata.all()
            context["tags"] = [
                {
                    "text": x.name,
                    "value": x.name,
                    "is_meta": x.is_meta
                } for x in linked_blob.tags.all()
            ]

        if "linked_collection" in self.request.GET:
            collection = Collection.objects.get(user=self.request.user, uuid=self.request.GET["linked_collection"])
            context["linked_collection_info"] = collection
            context["linked_collection_blob_list"] = collection.blobs.all()

            # Grab the initial metadata and tags from one of the other blobs in the collection
            context["metadata"] = context["linked_collection_blob_list"][0].metadata.all()
            context["tags"] = [
                {
                    "text": x.name,
                    "value": x.name,
                    "is_meta": x.is_meta
                } for x in context["linked_collection_blob_list"][0].tags.all()
            ]

        if "collection_uuid" in self.request.GET:
            context["collection_info"] = Collection.objects.get(user=self.request.user, uuid=self.request.GET["collection_uuid"])

        # In case of a form error, we need to return the user's
        #  submitted data by populating some of the form fields
        #  that aren't handled automatically by Django's form object.
        #  Some fields are also handled in form_invalid().
        context["metadata"] = get_metadata_from_form(self.request)

        if self.request.POST.get("tags", "") != "":
            context["tags"] = [
                {"text": x}
                for x in self.request.POST["tags"].split(",")
            ]

        if self.request.POST.get("is_book", "") == "on":
            context["is_book"] = True

        context["title"] = "Create Blob"

        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if "is_note" in self.request.GET:
            form.initial["is_note"] = True

        if "linked_blob" in self.request.GET:
            blob = Blob.objects.get(user=self.request.user, pk=int(self.request.GET.get("linked_blob")))
            form.initial["tags"] = ",".join([x.name for x in blob.tags.all()])
            form.initial["date"] = blob.date
            form.initial["name"] = blob.name

        if "linked_collection" in self.request.GET:
            collection_uuid = self.request.GET["linked_collection"]
            blob_uuid = Collection.objects.get(user=self.request.user, uuid=collection_uuid).blobs.all()[0].uuid
            blob = Blob.objects.get(user=self.request.user, uuid=blob_uuid)
            form.initial["date"] = blob.date
            form.initial["name"] = blob.name

        return form

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.file_modified = form.cleaned_data['file_modified']
        obj.save()

        # Save the tags
        form.save_m2m()

        handle_metadata(obj, self.request)

        if "linked_blob_uuid" in self.request.POST:
            linked_blob = Blob.objects.get(uuid=self.request.POST["linked_blob_uuid"])
            obj.blobs.add(linked_blob)

        handle_linked_collection(obj, self.request)

        if "collection_uuid" in self.request.POST:
            obj.add_to_collection(self.request.user, self.request.POST.get("collection_uuid"))

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

        RecentlyViewedBlob.add(self.request.user, self.object)

        context["metadata"], context["urls"] = self.object.get_metadata()

        context["metadata_misc"] = json.dumps(
            {
                key: value for (key, value)
                in context["metadata"].items()
                if key not in
                [
                    "is_book",
                    "Url",
                    "Publication Date",
                    "Subtitle",
                    "Name",
                    "Author"
                ]
            }
        )

        context["date"] = self.object.get_date()

        if self.object.sha1sum:
            context["aws_url"] = f"https://s3.console.aws.amazon.com/s3/buckets/{settings.AWS_STORAGE_BUCKET_NAME}/blobs/{self.object.uuid}/"

        if self.object.is_note:
            context["is_pinned_note"] = self.object.is_pinned_note()

        try:

            context["elasticsearch_info"] = json.dumps(self.object.get_elasticsearch_info())

        except IndexError:

            # Give Elasticsearch up to a minute to index the blob
            if int(datetime.datetime.now().strftime("%s")) - int(self.object.created.strftime("%s")) > 60:
                messages.add_message(self.request, messages.ERROR, "Blob not found in Elasticsearch")

        context["caption"] = self.object.get_name(remove_edition_string=True)

        context["linked_blobs"] = self.object.get_linked_blobs()

        context["collection_list"] = self.object.get_collection_info()

        if "content_type" in context or self.object.sha1sum or context["metadata_misc"] != "{}":
            context["show_metadata"] = True
        else:
            context["show_metadata"] = False

        context["related_questions"] = self.object.question_set.all()

        context["tree"] = json.dumps(
            {
                "label": "Root",
                "nodes": self.object.get_tree()
            }
        )

        return context

    def get_queryset(self):
        return Blob.objects.filter(user=self.request.user)


@method_decorator(login_required, name="dispatch")
class BlobUpdateView(FormRequestMixin, UpdateView):
    template_name = "blob/update.html"
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sha1sum"] = self.kwargs.get("sha1sum")

        if self.object.sha1sum:
            context["cover_url"] = self.object.get_cover_url()

        context["metadata"] = self.object.metadata.exclude(name="is_book")

        if [x for x in self.object.metadata.all() if x.name == "is_book"]:
            context["is_book"] = True

        context["collections_other"] = Collection.objects.filter(Q(user=self.request.user)
                                                                 & ~Q(blobs__uuid=self.object.uuid)
                                                                 & Q(is_private=False))
        context["action"] = "Update"
        context["title"] = "Blob Update :: {}".format(self.object.get_name(remove_edition_string=True))
        context["tags"] = [{"text": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
        return context

    def get(self, request, **kwargs):
        self.object = Blob.objects.get(user=self.request.user, uuid=self.kwargs.get("uuid"))
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object, form=form)
        return render(request, self.template_name, context)

    def get_object(self, queryset=None):
        return Blob.objects.get(user=self.request.user, uuid=self.kwargs.get("uuid"))

    def form_valid(self, form):
        blob = form.instance

        file_changed = False if "file" not in form.changed_data else True

        # Only check for a renamed file if the file itself hasn't changed
        if not file_changed:
            old_filename = str(form.instance.file)
            new_filename = form.cleaned_data["filename"]

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

        blob.file_modified = form.cleaned_data["file_modified"]

        # Delete all existing tags
        blob.tags.clear()

        handle_metadata(blob, self.request)

        self.object = form.save()

        self.object.index_blob(file_changed, new_blob=False)

        messages.add_message(self.request, messages.INFO, "Blob updated")

        return HttpResponseRedirect(reverse("blob:detail", kwargs={"uuid": str(blob.uuid)}))


@method_decorator(login_required, name="dispatch")
class BlobCloneView(View):

    def get(self, request, *args, **kwargs):
        original_blob = Blob.objects.get(uuid=kwargs["uuid"])
        new_blob = original_blob.clone()
        messages.add_message(self.request, messages.INFO, "New blob successfully cloned")
        return HttpResponseRedirect(reverse("blob:detail", kwargs={"uuid": new_blob.uuid}))


@method_decorator(login_required, name="dispatch")
class BlobImportView(View):
    template_name = "blob/import.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):

        url = request.POST.get("url", None)

        try:
            blob_uuid = import_blob(request.user, url)
        except Exception as e:
            messages.add_message(request, messages.ERROR, e)

        if not messages.get_messages(request):
            return HttpResponseRedirect(reverse("blob:detail", kwargs={"uuid": blob_uuid}))
        else:
            context = {
                "hide_messages": True
            }
            return render(request, self.template_name, context)


# Metadata objects are not handled by the form -- handle them manually
def handle_metadata(blob, request):

    metadata_old = blob.metadata.all()
    for i in metadata_old:
        i.delete()

    metadata = get_metadata_from_form(request)
    for pair in metadata:
        new_metadata, created = MetaData.objects.get_or_create(
            blob=blob,
            user=request.user,
            name=pair["name"],
            value=pair["value"]
        )
        if created:
            new_metadata.save()

    if request.POST.get("is_book", ""):
        new_metadata = MetaData(user=request.user, name="is_book", value="true", blob=blob)
        new_metadata.save()


def get_metadata_from_form(request):
    """
    Extract metadata from POST args into a list
    """
    metadata = []

    p = re.compile(r"^\d+_(.*)")

    for key, value in request.POST.items():
        m = p.match(key)
        if m:
            name = m.group(1).strip()
            value = value.strip()
            if name == "" or value == "":
                continue
            metadata.append(
                {
                    "name": name,
                    "value": value
                }
            )

    return metadata


def handle_linked_collection(blob, request):

    if "linked_collection" in request.POST:
        collection = Collection.objects.get(user=request.user, uuid=request.POST["linked_collection"])
        collection.add_blob(blob)


@login_required
def metadata_name_search(request):

    m = MetaData.objects.filter(user=request.user).values("name").filter(name__icontains=request.GET["query"]).distinct("name").order_by("name".lower())

    return_data = [{"value": x["name"]} for x in m]

    return JsonResponse(return_data, safe=False)


@login_required
def collection_mutate(request):

    blob_uuid = request.POST["blob_uuid"]
    collection = Collection.objects.get(user=request.user, uuid=request.POST["collection_uuid"])
    mutation = request.POST["mutation"]

    if mutation == "add":

        if SortOrderCollectionBlob.objects.filter(collection=collection, blob__uuid=blob_uuid).exists():
            message = f"Blob already in collection '{collection.name}'"
        else:
            blob = Blob.objects.get(uuid=blob_uuid)
            blob.add_to_collection(request.user, collection.uuid)
            message = f"Added to collection '{collection.name}'"

    elif mutation == "delete":
        blob = Blob.objects.get(uuid=blob_uuid)
        blob.delete_from_collection(request.user, collection.uuid)
        message = f"Removed from collection '{collection.name}'"

    return JsonResponse({"status": "OK", "message": message}, safe=False)


@login_required
def parse_date(request, input_date):

    error = None
    response = ""

    try:
        response = parse_date_from_string(input_date)
    except ValueError as e:
        error = str(e)

    return JsonResponse({"output_date": response,
                         "error": error})


@login_required
def recent_blobs(request):

    blob_list, doctypes = get_recent_blobs(request.user)

    response = {
        "blobList": blob_list,
        "docTypes": doctypes,
        "status": "OK"
    }

    return JsonResponse(response, safe=False)


@login_required
def get_elasticsearch_info(request, uuid):
    """
    Get the Elasticsearch entry for a blob.
    Return an empty dict if not present.
    """

    blob = Blob.objects.get(uuid=uuid)

    try:
        info = blob.get_elasticsearch_info()
    except IndexError:
        info = {}

    response = {
        "info": info,
        "status": "OK"
    }

    return JsonResponse(response, safe=False)


def get_related_blobs(request, uuid):
    """
    Get all related blobs for a given blob.
    """

    blob = Blob.objects.get(uuid=uuid, user=request.user)

    response = {
        "status": "OK",
        "blob_list": blob.get_related_blobs(),
    }

    return JsonResponse(response)


def link(request):
    """
    Add a relationshiop between two blobs.
    """

    blob_1_uuid = request.POST["blob_1_uuid"]
    blob_2_uuid = request.POST["blob_2_uuid"]

    blob_1 = Blob.objects.get(uuid=blob_1_uuid)
    blob_2 = Blob.objects.get(uuid=blob_2_uuid)

    blob_1.blobs.add(blob_2)

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


def unlink(request):
    """
    Remove a relationship between two blobs.
    """

    blob_1_uuid = request.POST["blob_1_uuid"]
    blob_2_uuid = request.POST["blob_2_uuid"]

    blob_1 = Blob.objects.get(uuid=blob_1_uuid)
    blob_2 = Blob.objects.get(uuid=blob_2_uuid)

    blob_1.blobs.remove(blob_2)

    response = {
        "status": "OK",
    }

    return JsonResponse(response)
