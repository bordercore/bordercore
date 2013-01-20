from feed.models import *
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from django.shortcuts import get_list_or_404, render_to_response
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from pprint import pprint

from subprocess import call

@login_required
def feed_list(request):

    import json

    feeds = FeedItem.objects.select_related().filter(feed__id__in=[110,121,1,97,119,117,106,120,118,113,115,63,62,68,101,5,78,116,103,56,99,73,92,114,108,37,90,102,100,53,104,9,112,109,105,36,107,93,79,6,98,51,52,65,20,80,70,71,75,61,4,33,38,48,11,76,86,88,85,82,10,89,64,66,91,95])

    feed_all = {}
    feed_info = []

    for feed in feeds:
        if feed.feed.id in feed_all:
            feed_all[ feed.feed.id ]['links'].append( { 'id': feed.feed.id, 'name': feed.feed.name, 'link': feed.link, 'title': feed.title } )
        else:
            feed_all[ feed.feed_id ] = { 'links': [ { 'id': feed.feed.id, 'name': feed.feed.name, 'link': feed.link, 'title': feed.title } ], 'name': feed.feed.name, 'feed_homepage': feed.feed.homepage }

    for feed in feeds.distinct('feed__name'):
        feed_info.append( { 'id': feed.feed.id, 'name': feed.feed.name } )

    return render_to_response('feed/index.html',
                              {'section': 'Feeds', 'feed_info': feed_info, 'json': json.dumps(feed_all) },
                              context_instance=RequestContext(request))
