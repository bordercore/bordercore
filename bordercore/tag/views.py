from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect

from tag.models import Tag
from tag.services import search as search_service


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
