from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

#from homepage.models import Homepage

SECTION = 'Home'

@login_required
def homepage(request):

    return render_to_response('homepage/index.html',
                              {'section': SECTION },
                              context_instance=RequestContext(request))
