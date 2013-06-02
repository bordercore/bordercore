from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from quote.models import Quote

SECTION = 'Home'

@login_required
def homepage(request):

    quote = Quote.objects.order_by('?')[0]

    return render_to_response('homepage/index.html',
                              {'section': SECTION, 'quote': quote },
                              context_instance=RequestContext(request))
