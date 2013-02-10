from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

#from homepage.models import Homepage


@login_required
def homepage(request):

    return render_to_response('homepage/index.html',
                              {'section': 'Home' },
                              context_instance=RequestContext(request))
