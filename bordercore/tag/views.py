import urllib

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect

from accounts.models import SortOrder
from tag.models import Tag, TagAlias


@login_required
def tag_search(request):

    args = {}

    # Only retrieve tags which have been applied to at least one note
    if request.GET.get('type') == 'note':
        args['blob__is_note'] = True

    query = urllib.parse.unquote(request.GET.get('query', ''))

    tag_list = [{'name': x.name, 'value': x.name, 'is_meta': x.is_meta} for x in
                Tag.objects.filter(Q((Q(bookmark__user=request.user) & Q(name__icontains=query)))
                                   | Q((Q(blob__user=request.user) & Q(name__icontains=query)))
                                   | Q((Q(collection__user=request.user) & Q(name__icontains=query)))
                                   | Q((Q(question__user=request.user) & Q(name__icontains=query)))
                                   | Q((Q(song__user=request.user) & Q(name__icontains=query)))
                                   | Q((Q(todo__user=request.user) & Q(name__icontains=query))), **args).distinct('name')]

    tag_alias_list = [{"name": f"{x.name} ({x.tag.name})", "value": x.tag.name, "is_alias": True} for x in
                      TagAlias.objects.filter(Q(user=request.user) & Q(name__icontains=query))]

    tag_alias_list.extend(tag_list)
    return JsonResponse(tag_alias_list, safe=False)


@login_required
def add_favorite_tag(request):

    tag = request.POST['tag']

    tag_object = Tag.objects.get(name=tag)
    c = SortOrder(user_profile=request.user.userprofile, tag=tag_object)
    c.save()

    return redirect('bookmark_tag', tag_filter=tag)


@login_required
def remove_favorite_tag(request):

    tag = request.POST['tag']

    tag_object = Tag.objects.get(name=tag)

    old_position = SortOrder.objects.get(user_profile=request.user.userprofile, tag=tag_object)

    old_position.delete()

    return redirect('bookmark_overview')
