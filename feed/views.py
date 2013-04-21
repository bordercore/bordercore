from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from feed.models import Feed, FeedItem

SECTION = 'Feeds'

@login_required
def feed_list(request):

    default_feed_id = Feed.objects.get(name='Hacker News').id
    current_feed = request.session.get('current_feed', default_feed_id)

    import json

    feeds = FeedItem.objects.select_related().filter(feed__id__in=request.user.userprofile.rss_feeds.split(','))

    feed_all = {}

    for feed in feeds:
        data = { 'id': feed.feed.id, 'name': feed.feed.name, 'link': feed.link, 'title': feed.title }
        if feed.feed.id in feed_all:
            feed_all[ feed.feed.id ]['links'].append( data )
        else:
            feed_all[ feed.feed_id ] = { 'links': [ data ], 'name': feed.feed.name, 'feed_homepage': feed.feed.homepage }

    # We can't merely use Feed.objects.filter(), since this won't retrieve our feeds in
    #  the correct order (based on the order of the feed ids in userprofile.rss_feeds)
    #  So we store the feed name temporarily in a lookup table...
    lookup = {}
    for feed in Feed.objects.filter(id__in=request.user.userprofile.rss_feeds.split(',')):
        lookup[ feed.id ] = feed.name

    # ...then use that here, where the proper order is preserved
    feed_info = []
    for feed_id in request.user.userprofile.rss_feeds.split(','):
        feed_info.append( { 'id': int(feed_id), 'name': lookup[ int(feed_id) ] } )

    return render_to_response('feed/index.html',
                              {'section': SECTION, 'feed_info': feed_info, 'json': json.dumps(feed_all), 'current_feed': current_feed },
                              context_instance=RequestContext(request))


def set_current_feed(request, feed_id):

    request.session['current_feed'] = feed_id

    return render_to_response('feed/set_current_feed.json',
                              {'section': SECTION  },
                              context_instance=RequestContext(request))


def sort_feed(request):

    feed_id = int(request.POST['feed_id'])
    new_position = int(request.POST['position'])

    feeds = [ int(t.strip()) for t in request.user.userprofile.rss_feeds.split(',') ]

    # First remove the feed item from the list
    feeds.remove( feed_id )

    # Then re-insert it in its new position
    feeds.insert( new_position - 1, feed_id )

    request.user.userprofile.rss_feeds = ','.join( [ str(feed_id) for feed_id in feeds ] )
    request.user.userprofile.save()

    # TODO: Return JSON response here rather than an actual web page

    return render_to_response('feed/set_current_feed.json',
                              {'section': SECTION  },
                              context_instance=RequestContext(request))
