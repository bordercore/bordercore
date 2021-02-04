from botocore.errorfactory import ClientError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
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

IMAGE_TYPE_LIST = ["jpeg", "gif", "png"]


@method_decorator(login_required, name="dispatch")
class CollectionListView(FormMixin, ListView):

    context_object_name = "info"
    form_class = CollectionForm

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in CollectionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super(CollectionListView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user). \
            filter(is_private=False). \
            prefetch_related("tags")

    def get_context_data(self, **kwargs):
        context = super(CollectionListView, self).get_context_data(**kwargs)

        info = []

        for myobject in context["object_list"]:
            info.append(dict(name=myobject.name,
                             tags=myobject.get_tags(),
                             updated=myobject.get_modified(),
                             unixtime=format(myobject.modified, "U"),
                             objectcount=len(myobject.blob_list) if myobject.blob_list else 0,
                             id=myobject.uuid))

        context["cols"] = ["name", "tags", "updated", "unixtime", "objectcount", "id"]
        context["info"] = info
        context["title"] = "Collection List"

        return context


@method_decorator(login_required, name="dispatch")
class CollectionDeleteView(DeleteView):

    def get_object(self, queryset=None):
        return Collection.objects.get(user=self.request.user, uuid=self.kwargs.get("collection_uuid"))

    def get_success_url(self):
        messages.add_message(
            self.request,
            messages.INFO, f"Collection <strong>{self.object.name}</strong> deleted",
            extra_tags="show_in_dom"
        )
        return reverse("collection:list")


@method_decorator(login_required, name="dispatch")
class CollectionDetailView(DetailView):

    model = Collection
    slug_field = "uuid"
    slug_url_kwarg = "collection_uuid"

    def get_context_data(self, **kwargs):
        context = super(CollectionDetailView, self).get_context_data(**kwargs)

        blob_list = self.object.get_blob_list()

        if blob_list:
            context["blob_list"] = blob_list
            try:
                context["first_blob_cover_info"] = Blob.get_cover_info_static(user=self.request.user, sha1sum=context["blob_list"].first().sha1sum)
            except ClientError:
                pass

        context["nav"] = "collection"
        context["title"] = f"Collection Detail :: {self.object.name}"

        return context


@method_decorator(login_required, name="dispatch")
class CollectionCreateView(CreateView):
    template_name = "collection/collection_list.html"
    form_class = CollectionForm

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in CollectionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super(CollectionCreateView, self).get_form_kwargs()
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
    success_url = reverse_lazy("collection:list")
    slug_field = "uuid"
    slug_url_kwarg = "collection_uuid"

    # Override this method so that we can pass the request object to the form
    #  so that we have access to it in CollectionForm.__init__()
    def get_form_kwargs(self):
        kwargs = super(CollectionUpdateView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_queryset(self):
        base_qs = super(CollectionUpdateView, self).get_queryset()
        return base_qs.filter(user=self.request.user)

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.user = self.request.user

        # Delete all existing tags first
        obj.tags.clear()

        # Then add all tags specified
        for tag in form.cleaned_data["tags"]:
            obj.tags.add(tag)

        obj.save()

        return HttpResponseRedirect(self.get_success_url())


@login_required
def get_info(request):

    from django.core.exceptions import ObjectDoesNotExist

    info = ""

    try:
        if request.GET.get("query_type", "") == "uuid":
            match = Collection.objects.get(user=request.user, uuid=request.GET["uuid"])
        else:
            match = Collection.objects.get(user=request.user, name=request.GET["name"])
        if match:
            info = {
                "name": match.name,
                "description": match.description,
                "uuid": match.uuid,
                "tags": [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in match.tags.all()]
            }
    except ObjectDoesNotExist:
        info = {}

    return JsonResponse(info)


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
