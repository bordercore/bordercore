from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from tag.models import Tag
import json

@login_required
def tag_search(request):

    args = {}

    # Only retrieve tags which have been applied to at least one blog post
    if request.GET.get('type') == 'blog':
        args['post__isnull'] = False

    tag_list = [{'value':x.name} for x in Tag.objects.filter(name__istartswith=request.GET.get('query', ''), **args).distinct('name')]

    return render_to_response('return_json.json',
                              {'info': json.dumps(tag_list)},
                              context_instance=RequestContext(request),
                              content_type="application/json")
