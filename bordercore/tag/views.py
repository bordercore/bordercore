import urllib

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect

from tag.models import Tag


@login_required
def tag_search(request):

    query = urllib.parse.unquote(request.GET.get("query", None))

    results = Tag.search(request.user, query, request.GET.get("type", None) == "note")

    return JsonResponse(results, safe=False)


@login_required
def add_favorite_tag(request):

    tag_name = request.POST["tag"]

    tag = Tag.objects.get(name=tag_name, user=request.user)
    tag.add_favorite_tag()

    return redirect("bookmark:overview")


@login_required
def remove_favorite_tag(request):

    tag_name = request.POST["tag"]

    tag = Tag.objects.get(name=tag_name, user=request.user)
    tag.remove_favorite_tag()

    return redirect("bookmark:overview")
