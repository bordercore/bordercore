from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from .models import Tag, TagAlias
from .services import get_random_tag_info
from .services import search as search_service


@login_required
def pin(request):

    tag_name = request.POST["tag"]

    tag = Tag.objects.get(name=tag_name, user=request.user)
    tag.pin()

    return redirect("bookmark:overview")


@login_required
def unpin(request):

    tag_name = request.POST["tag"]

    tag = Tag.objects.get(name=tag_name, user=request.user)
    tag.unpin()

    return redirect("bookmark:overview")


@login_required
def search(request):

    tag_name = request.GET["query"].lower()
    doctype = request.GET.get("doctype", None)

    matches = search_service(request.user, tag_name, doctype)

    return JsonResponse(matches, safe=False)


@method_decorator(login_required, name="dispatch")
class TagListView(ListView):

    model = TagAlias
    template_name = "tag/tag_list.html"

    def get_queryset(self):
        return TagAlias.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return {
            "random_tag_info": get_random_tag_info(self.request.user),
            **context,
        }


@login_required
def add_alias(request):

    tag_name = request.POST["tag_name"]
    alias_name = request.POST["alias_name"]

    # Check that the alias doesn't already exist
    if TagAlias.objects.filter(name=alias_name):
        response = {
            "status": "Warning",
            "message": "Alias already exists"
        }
    elif Tag.objects.filter(name=alias_name):
        response = {
            "status": "Warning",
            "message": f"A tag with the name '{alias_name}' already exists"
        }
    else:

        tag = Tag.objects.get(name=tag_name, user=request.user)
        tag_alias = TagAlias(name=alias_name, tag=tag, user=request.user)
        tag_alias.save()
        response = {
            "status": "OK",
            "message": ""
        }

    return JsonResponse(response)
