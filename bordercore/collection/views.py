import json

from botocore.errorfactory import ClientError
from rest_framework.decorators import api_view

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Exists, OuterRef
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import (CreateView, DeleteView, FormMixin,
                                       UpdateView)
from django.views.generic.list import ListView

from collection.forms import CollectionForm
from collection.models import Collection, SortOrderCollectionBlob
from lib.mixins import FormRequestMixin


@method_decorator(login_required, name="dispatch")
class CollectionListView(FormRequestMixin, FormMixin, ListView):

    form_class = CollectionForm

    def get_queryset(self):

        query = Collection.objects.filter(user=self.request.user). \
            filter(is_private=False)

        if "query" in self.request.GET:
            query = query.filter(name__icontains=self.request.GET.get("query"))

        query = query.annotate(num_blobs=Count("blobs"))

        query = query.order_by("-modified")

        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["cover_url"] = settings.COVER_URL
        context["title"] = "Collection List"

        return context


@method_decorator(login_required, name="dispatch")
class CollectionDetailView(FormRequestMixin, FormMixin, DetailView):

    model = Collection
    slug_field = "uuid"
    slug_url_kwarg = "collection_uuid"
    form_class = CollectionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        blob_list = self.object.get_blob_list()

        if blob_list:
            context["blob_list"] = blob_list
            try:
                context["first_blob_info"] = json.dumps(self.object.get_blob(0, False))
            except ClientError:
                pass

        context["tags"] = [
            {
                "text": x.name,
                "value": x.name,
                "is_meta": x.is_meta
            } for x in self.object.tags.all()
        ]

        context["title"] = f"Collection Detail :: {self.object.name}"

        return context


@method_decorator(login_required, name="dispatch")
class CollectionCreateView(FormRequestMixin, CreateView):
    template_name = "collection/collection_list.html"
    form_class = CollectionForm

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
class CollectionUpdateView(FormRequestMixin, UpdateView):

    model = Collection
    form_class = CollectionForm
    slug_field = "uuid"
    slug_url_kwarg = "collection_uuid"

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

    collection_uuid = request.POST["collection_uuid"]
    blob_uuid = request.POST["blob_uuid"]
    new_position = int(request.POST["position"])

    so = SortOrderCollectionBlob.objects.get(collection__uuid=collection_uuid, blob__uuid=blob_uuid)
    SortOrderCollectionBlob.reorder(so, new_position)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def get_blob(request, collection_uuid, blob_position):

    collection = Collection.objects.get(uuid=collection_uuid)

    randomize = True if request.GET.get("randomize", "") == "true" else False
    return JsonResponse(collection.get_blob(blob_position, randomize))


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


@login_required
def search(request):

    query = Collection.objects.filter(user=request.user). \
        filter(is_private=False)

    if "query" in request.GET:
        query = query.filter(name__icontains=request.GET.get("query"))

    if "blob_uuid" in request.GET:
        query = query.filter(blobs__uuid__in=[request.GET.get("blob_uuid")])

    if "exclude_blob_uuid" in request.GET:
        contains_blob = Collection.objects.filter(uuid=OuterRef("uuid")) \
                                          .filter(blobs__uuid__in=[request.GET.get("exclude_blob_uuid")])
        query = query.annotate(contains_blob=Exists(contains_blob))

    query = query.annotate(num_blobs=Count("blobs"))

    collection_list = query.order_by("-modified")

    return JsonResponse(
        [
            {
                "name": x.name,
                "uuid": x.uuid,
                "num_blobs": x.num_blobs,
                "url": reverse("collection:detail", kwargs={"collection_uuid": x.uuid}),
                "cover_url": f"{settings.COVER_URL}collections/{x.uuid}.jpg",
                "contains_blob": getattr(x, "contains_blob", None)
            }
            for x in collection_list
        ],
        safe=False
    )


@login_required
def get_blob_list(request, collection_uuid):

    collection = Collection.objects.get(uuid=collection_uuid)
    blob_list = collection.get_blob_list()

    return JsonResponse(blob_list, safe=False)
