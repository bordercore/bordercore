from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import redirect

from accounts.models import SortOrder
from tag.models import Tag


@login_required
def tag_search(request):

    args = {}

    # Only retrieve tags which have been applied to at least one blog post
    if request.GET.get('type') == 'blog':
        args['document__is_blog'] = True

    query = request.GET.get('query', '')
    tag_list = [{'value': x.name, 'is_meta': x.is_meta} for x in
                Tag.objects.filter(Q((Q(bookmark__user=request.user) & Q(name__icontains=query))) |
                                   Q((Q(document__user=request.user) & Q(name__icontains=query))) |
                                   Q((Q(collection__user=request.user) & Q(name__icontains=query))) |
                                   Q((Q(collection__user=request.user) & Q(name__icontains=query))) |
                                   Q((Q(song__user=request.user) & Q(name__icontains=query))) |
                                   Q((Q(todo__user=request.user) & Q(name__icontains=query))), **args).distinct('name')]

    return JsonResponse(tag_list, safe=False)


def add_favorite_tag(request):

    tag = request.POST['tag']

    tag_object = Tag.objects.get(name=tag)
    c = SortOrder(user_profile=request.user.userprofile, tag=tag_object)
    c.save()

    return redirect('bookmark_tag', tag_filter=tag)
