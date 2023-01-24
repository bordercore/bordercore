import datetime
import json
import logging
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, ModelFormMixin, UpdateView
from django.views.generic.list import ListView

from blob.forms import BlobForm
from blob.models import Blob, BlobBlob, MetaData, RecentlyViewedBlob
from blob.services import import_blob
from collection.models import Collection, CollectionObject
from lib.mixins import FormRequestMixin
from lib.time_utils import parse_date_from_string

log = logging.getLogger(f"bordercore.{__name__}")


class FormValidMixin(ModelFormMixin):
    """
    A mixin to encapsulate common logic used in Update and Create views
    """

    def form_valid(self, form):

        new_object = not self.object

        blob = form.save(commit=False)

        # Only rename a blob's file if the file itself hasn't changed
        if "file" not in form.changed_data and form.cleaned_data["filename"] != blob.file.name:
            blob.rename_file(form.cleaned_data["filename"])

        blob.user = self.request.user
        blob.file.name = form.cleaned_data["filename"]
        blob.file_modified = form.cleaned_data["file_modified"]
        blob.save()

        # Save the tags
        form.save_m2m()

        handle_metadata(blob, self.request)

        if new_object:
            if "linked_blob_uuid" in self.request.POST:
                linked_blob = Blob.objects.get(uuid=self.request.POST["linked_blob_uuid"])
                blob.blobs.add(linked_blob)

            handle_linked_collection(blob, self.request)

            if "collection_uuid" in self.request.POST:
                collection = Collection.objects.get(uuid=self.request.POST.get("collection_uuid"), user=self.request.user)
                collection.add_object(blob)

        blob.index_blob()

        message = "Blob created" if new_object else "Blob updated"
        messages.add_message(self.request, messages.INFO, message)

        return JsonResponse({"status": "OK", "uuid": blob.uuid})

    def form_invalid(self, form):
        """If the form is invalid, return a list of errors."""

        return JsonResponse(form.errors, status=400)


@method_decorator(login_required, name="dispatch")
class BlobListView(ListView):

    model = Blob

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return {
            **context,
            "title": "Recent Blobs"
        }


@method_decorator(login_required, name="dispatch")
class BlobCreateView(FormRequestMixin, CreateView, FormValidMixin):
    template_name = "blob/update.html"
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"

        if "linked_blob_uuid" in self.request.GET:
            linked_blob = Blob.objects.get(user=self.request.user, uuid=self.request.GET["linked_blob_uuid"])
            context["linked_blob"] = linked_blob
            context["linked_blob"].thumbnail_url = linked_blob.get_cover_url_small()

            # Grab the initial metadata and tags from the linked blob
            context["metadata"] = linked_blob.metadata.all()
            context["tags"] = [x.name for x in linked_blob.tags.all()]

        if "linked_collection" in self.request.GET:
            context["linked_collection"] = Collection.objects.get(
                user=self.request.user,
                uuid=self.request.GET["linked_collection"]
            )
            context["tags"] = [
                x.name
                for x in CollectionObject.objects.filter(
                        collection__uuid=self.request.GET["linked_collection"]
                ).first().blob.tags.all()
            ]

        if "collection_uuid" in self.request.GET:
            context["collection_info"] = Collection.objects.get(user=self.request.user, uuid=self.request.GET["collection_uuid"])

        # In case of a form error, we need to return the user's
        #  submitted data by populating some of the form fields
        #  that aren't handled automatically by Django's form object.
        #  Some fields are also handled in form_invalid().
        context["metadata"] = get_metadata_from_form(self.request)

        if "tags" in self.request.POST:
            context["tags"] = [
                {"text": x}
                for x in self.request.POST["tags"].split(",")
            ]

        context["is_book"] = self.request.POST.get("is_book", "") == "on"

        context["title"] = "Create Blob"

        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if "is_note" in self.request.GET:
            form.initial["is_note"] = True
            form.initial["math_support"] = True

        if "linked_blob" in self.request.GET:
            blob = Blob.objects.get(user=self.request.user, pk=int(self.request.GET.get("linked_blob")))
            form.initial["tags"] = ",".join([x.name for x in blob.tags.all()])
            form.initial["date"] = blob.date
            form.initial["name"] = blob.name

        if "linked_collection" in self.request.GET:
            collection_uuid = self.request.GET["linked_collection"]
            so = CollectionObject.objects.filter(collection__uuid=collection_uuid).first()
            form.initial["date"] = so.blob.date
            form.initial["name"] = so.blob.name

        return form


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

        context["linked_objects"] = self.object.get_linked_objects()

        context["collection_list"] = self.object.get_collection_info()

        context["show_metadata"] = "content_type" in context \
            or self.object.sha1sum \
            or context["metadata_misc"] != "{}"

        related_objects = self.object.bcobject_set
        if related_objects.first():
            context["related_questions"] = related_objects.first().bc_objects.all()
        else:
            context["related_questions"] = []

        context["tree"] = json.dumps(
            {
                "label": "Root",
                "nodes": self.object.get_tree()
            }
        )

        context["name"] = self.object.get_name(remove_edition_string=True)

        return context

    def get_queryset(self):
        return Blob.objects.filter(user=self.request.user)


@method_decorator(login_required, name="dispatch")
class BlobUpdateView(FormRequestMixin, UpdateView, FormValidMixin):
    template_name = "blob/update.html"
    form_class = BlobForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sha1sum"] = self.kwargs.get("sha1sum")

        if self.object.sha1sum:
            context["cover_url"] = self.object.get_cover_url()

        context["metadata"] = self.object.metadata.exclude(name="is_book")

        context["is_book"] = self.object.metadata.filter(name="is_book").exists()

        context["collections_other"] = Collection.objects.filter(Q(user=self.request.user)
                                                                 & ~Q(collectionobject__blob__uuid=self.object.uuid)
                                                                 & Q(is_private=False))
        context["action"] = "Update"
        context["title"] = "Blob Update :: {}".format(self.object.get_name(remove_edition_string=True))
        context["tags"] = [x.name for x in self.object.tags.all()]
        return context

    def get(self, request, **kwargs):
        self.object = Blob.objects.get(user=self.request.user, uuid=self.kwargs.get("uuid"))
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object, form=form)
        return render(request, self.template_name, context)

    def get_object(self, queryset=None):
        return Blob.objects.get(user=self.request.user, uuid=self.kwargs.get("uuid"))


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
            blob = import_blob(request.user, url)
        except Exception as e:
            messages.add_message(request, messages.ERROR, e)

        if not messages.get_messages(request):
            return HttpResponseRedirect(reverse("blob:detail", kwargs={"uuid": blob.uuid}))
        else:
            return render(request, self.template_name, {})


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
        collection.add_object(blob)


@login_required
def metadata_name_search(request):

    m = MetaData.objects.filter(user=request.user).values("name").filter(name__icontains=request.GET["query"]).distinct("name").order_by("name".lower())

    return_data = [{"value": x["name"]} for x in m]

    return JsonResponse(return_data, safe=False)


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
def update_cover_image(request):
    """
    Update the blob's cover image
    """

    blob_uuid = request.POST["blob_uuid"]
    image = request.FILES["image"].read()

    blob = Blob.objects.get(uuid=blob_uuid)
    blob.update_cover_image(image)

    response = {
        "status": "OK"
    }

    return JsonResponse(response)


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

    blob_1 = Blob.objects.get(uuid=blob_1_uuid, user=request.user)
    blob_2 = Blob.objects.get(uuid=blob_2_uuid, user=request.user)

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

    blob_1 = Blob.objects.get(uuid=blob_1_uuid, user=request.user)
    blob_2 = Blob.objects.get(uuid=blob_2_uuid, user=request.user)

    # We don't know a priori which is blob_1 and which is blob_2,
    #  so try removing from both directions.
    blob_1.blobs.remove(blob_2)
    blob_2.blobs.remove(blob_1)

    response = {
        "status": "OK",
    }

    return JsonResponse(response)


def update_page_number(request):
    """
    Update the page number for a pdf that represents its cover image
    """

    blob_uuid = request.POST["blob_uuid"]
    page_number = int(request.POST["page_number"])

    blob = Blob.objects.get(uuid=blob_uuid)
    blob.update_page_number(page_number)

    response = {
        "message": "Cover image will be updated soon",
        "status": "OK"
    }

    return JsonResponse(response)


@login_required
def update_related_blob_note(request):

    blob_1_uuid = request.POST["blob_1_uuid"]
    blob_2_uuid = request.POST["blob_2_uuid"]
    note = request.POST["note"]

    bb = BlobBlob.objects.get(
        Q(
            Q(blob_1__uuid=blob_1_uuid) & Q(blob_2__uuid=blob_2_uuid)
        )
        | Q(
            Q(blob_1__uuid=blob_2_uuid) & Q(blob_2__uuid=blob_1_uuid)
        )
    )
    bb.note = note
    bb.save()

    response = {
        "status": "OK",
    }

    return JsonResponse(response)
