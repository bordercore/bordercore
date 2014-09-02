from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from tag.models import Tag
import json

@login_required
def tag_search(request):

    # Use this for the new Twitter typeahead
    # tag_list = [{'value':x.name} for x in Tag.objects.filter(name__istartswith=request.GET.get('query', '')).distinct('name')]

    # Use this for the typeahead included in Bootstrap 2
    tag_list = [x.name for x in Tag.objects.filter(name__istartswith=request.GET.get('query', '')).distinct('name')]

    return render_to_response('return_json.json',
                              {'info': json.dumps(tag_list)},
                              context_instance=RequestContext(request),
                              content_type="application/json")
