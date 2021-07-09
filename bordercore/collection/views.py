import re

from botocore.errorfactory import ClientError
from rest_framework.decorators import api_view

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect, JsonResponse
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

IMAGE_TYPE_LIST = ["jpeg", "gif", "png"]


@method_decorator(login_required, name="dispatch")
class CollectionListView(FormMixin, ListView):

    form_class = CollectionForm

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in CollectionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user). \
            filter(is_private=False). \
            prefetch_related("tags")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for collection in context["object_list"]:
            collection.updated = format(collection.modified, "Y-m-d")
            collection.objectcount = len(collection.blob_list) if collection.blob_list else 0
            collection.cover_url = f"{settings.COVER_URL}collections/{collection.uuid}.jpg",

        context["title"] = "Collection List"

        return context


@method_decorator(login_required, name="dispatch")
class CollectionDetailView(FormMixin, DetailView):

    model = Collection
    slug_field = "uuid"
    slug_url_kwarg = "collection_uuid"
    form_class = CollectionForm

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in CollectionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        blob_list = self.object.get_blob_list()

        for blob in blob_list:
            blob.name = re.sub("[\n\r]", "", blob.name)

        if blob_list:
            context["blob_list"] = blob_list
            try:
                context["first_blob_cover_info"] = Blob.get_cover_info_static(user=self.request.user, sha1sum=context["blob_list"].first().sha1sum)
            except ClientError:
                pass

        context["tags"] = [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in self.object.tags.all()]
        context["title"] = f"Collection Detail :: {self.object.name}"

        return context


@method_decorator(login_required, name="dispatch")
class CollectionCreateView(CreateView):
    template_name = "collection/collection_list.html"
    form_class = CollectionForm

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in CollectionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()

        # Take care of the tags.  Create any that are new.
        for tag in form.cleaned_data["tags"]:
            obj.tags.add(tag)

        obj.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("collection:list")


@method_decorator(login_required, name="dispatch")
class CollectionUpdateView(UpdateView):

    model = Collection
    form_class = CollectionForm
    slug_field = "uuid"
    slug_url_kwarg = "collection_uuid"

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in CollectionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(user=self.request.user)

    def form_valid(self, form):

        object = form.save(commit=False)
        object.user = self.request.user

        # Delete all existing tags first
        object.tags.clear()

        # Then add all tags specified
        for tag in form.cleaned_data["tags"]:
            object.tags.add(tag)

        object.save()

        messages.add_message(
            self.request,
            messages.INFO,
            "Collection updated"
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("collection:detail", kwargs={"collection_uuid": self.object.uuid})


@method_decorator(login_required, name='dispatch')
class CollectionDeleteView(DeleteView):

    model = Collection
    form_class = CollectionForm
    slug_field = "uuid"
    slug_url_kwarg = "collection_uuid"

    # Verify that the user is the owner of the task
    def get_object(self, queryset=None):
        obj = super().get_object()
        if not obj.user == self.request.user:
            raise Http404
        return obj

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.add_message(
            self.request,
            messages.INFO,
            f"Collection <strong>{self.object.name}</strong> deleted"
        )
        return response

    def get_success_url(self):
        return reverse("collection:list")


@login_required
def sort_collection(request):

    collection_id = int(request.POST["collection_id"])
    blob_id = int(request.POST["blob_id"])
    new_position = int(request.POST["position"])

    collection = Collection.objects.get(user=request.user, id=collection_id)

    collection.sort(blob_id, new_position)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def get_blob(request, collection_id, blob_position):

    collection = Collection.objects.get(pk=collection_id)

    return JsonResponse(collection.get_blob(blob_position))


@api_view(["GET"])
def get_images(request, collection_uuid):
    """
    Get four random blobs from a collection, to be used in
    creating a thumbnail image.
    """
    blob_list = Collection.objects.get(uuid=str(collection_uuid)).get_random_blobs()

    return JsonResponse(
        [
            {
                "uuid": x["uuid"],
                "filename": x["file"]
            }
            for x in blob_list
        ],
        safe=False
    )
