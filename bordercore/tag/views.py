from urllib.parse import unquote

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect

from tag.models import Tag


@login_required
def tag_search(request):

    query = unquote(request.GET.get("query", None))
    model_filter = request.GET.get("model_filter", None)

    results = Tag.search(
        request.user,
        query,
        request.GET.get("type", None) == "note",
        model_filter
    )

    return JsonResponse(results, safe=False)


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
