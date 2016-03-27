from bc_solr import *
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_list_or_404, render_to_response
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from subprocess import call

@login_required
def search(request):

    did_submit = False
#    if not request.user.is_authenticated():
#        return HttpResponseRedirect('/accounts/login/?next=%s' % request.path)
    message = ''
    results = ''
#    request.session["fav_color"] = "blue"
    if not request.user.is_authenticated():
        message = 'User is NOT authenticated'
    else:
        message = 'Hello ' + request.user.username

    if 'Go' in request.POST:
        did_submit = True
        mysolr = BCSolr()
        results = mysolr.search(request.POST['value'], "title")

#        message = 'Found something: ' + request.session['fav_color']
#        message = 'search for %s' % request.POST['value']
    return render_to_response('bcsolr/search.html',
                              {'message': message, 'results': results, 'did_submit': did_submit },
#                              {'message': message, 'results': results.results[0]['title'] },
                              context_instance=RequestContext(request))

