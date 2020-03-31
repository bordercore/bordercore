import json
import urllib

import feedparser
import requests

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from accounts.models import UserProfile
from feed.forms import FeedForm
from feed.models import Feed, FeedItem

# from feed.tasks import update_feed

SECTION = 'Feeds'


@method_decorator(login_required, name='dispatch')
class FeedListView(ListView):
    template_name = 'feed/index.html'
    context_object_name = 'feed_info'

    feed_all = None

    def get_queryset(self):
        default_feed_id = Feed.objects.get(name='Hacker News').id
        self.current_feed = self.request.session.get('current_feed', default_feed_id)

        feed_info = []

        if self.request.user.userprofile.rss_feeds:
            feeds = FeedItem.objects.select_related().filter(feed__id__in=self.request.user.userprofile.rss_feeds)

            feed_all = {}

            for feed in feeds:
                data = {'id': feed.feed.id, 'name': feed.feed.name, 'link': feed.link, 'title': feed.title}
                if feed.feed.id in feed_all:
                    feed_all[feed.feed.id]['links'].append(data)
                else:
                    feed_all[feed.feed_id] = {'links': [data], 'name': feed.feed.name, 'feed_homepage': feed.feed.homepage}

            self.feed_all = feed_all

            # We can't merely use Feed.objects.filter(), since this won't retrieve our feeds in
            #  the correct order (based on the order of the feed ids in userprofile.rss_feeds)
            #  So we store the feed name temporarily in a lookup table...
            lookup = {}
            for feed in Feed.objects.filter(id__in=self.request.user.userprofile.rss_feeds):
                lookup[feed.id] = feed

            # ...then use that here, where the proper order is preserved
            for feed_id in self.request.user.userprofile.rss_feeds:
                feed_info.append({'id': feed_id, 'feed': lookup[feed_id], 'name': lookup[feed_id].name})

        return feed_info

    def get_context_data(self, **kwargs):
        context = super(FeedListView, self).get_context_data(**kwargs)
        context['section'] = SECTION
        context['current_feed'] = self.current_feed
        context['json'] = json.dumps(self.feed_all)
        context['title'] = 'Feed List'
        return context


@method_decorator(login_required, name='dispatch')
class FeedSubscriptionListView(FeedListView):
    template_name = 'feed/subscriptions.html'
    context_object_name = 'feed_info'

    def get_queryset(self):

        # Get a list of all feeds not currently subscribed
        rss_feeds = self.request.user.userprofile.rss_feeds
        if rss_feeds is None:
            rss_feeds = []
        feeds_not_subscribed = Feed.objects.exclude(id__in=rss_feeds)
        self.feeds_not_subscribed = sorted(feeds_not_subscribed, key=lambda feed: feed.name.lower())
        return super(FeedSubscriptionListView, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(FeedSubscriptionListView, self).get_context_data(**kwargs)
        context['feeds_not_subscribed'] = self.feeds_not_subscribed
        context['title'] = 'Feeds :: Manage Subscriptions'
        return context


@login_required
def sort_feed(request):

    feed_id = int(request.POST['feed_id'])
    new_position = int(request.POST['position'])

    feeds = request.user.userprofile.rss_feeds

    # First remove the feed item from the list
    feeds.remove(feed_id)

    # Then re-insert it in its new position
    feeds.insert(new_position - 1, feed_id)

    request.user.userprofile.rss_feeds = feeds
    request.user.userprofile.save()

    return HttpResponse(json.dumps('OK'), content_type="application/json")


@login_required
def feed_subscribe(request):

    feed_id = int(request.POST['feed_id'])
    position = int(request.POST['position'])

    feed = Feed.objects.get(pk=feed_id)
    feed.subscribe_user(request.user, position)

    return HttpResponse(json.dumps('OK'), content_type="application/json")


@login_required
def feed_unsubscribe(request):

    feed_id = int(request.POST['feed_id'])

    feed = Feed.objects.get(pk=feed_id)
    feed.unsubscribe_user(request.user)

    return HttpResponse(json.dumps('OK'), content_type="application/json")


@login_required
def feed_edit(request, feed_id=None):

    f = None
    subscribers = None

    if feed_id:
        f = Feed.objects.get(pk=feed_id)
        action = 'Edit'
        title = 'Feed Edit :: {}'.format(f.name)
    else:
        action = 'Add'
        title = 'Feed Add'

    if request.method == 'POST':
        if request.POST['Go'] in ['Edit', 'Add']:
            form = FeedForm(request.POST, instance=f)  # A form bound to the POST data
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m()  # Save the many-to-many data for the form.

                # If this is a new feed, download the feed items
                if request.POST['Go'] == 'Add':
                    # update_feed.delay(newform.id)
                    # If the user clicked the 'subscribe' checkbox, subscribe her
                    if request.POST.get('subscribe', ''):
                        newform.subscribe_user(request.user, 1)

                # snarf_favicon.delay(b.url)
                messages.add_message(request, messages.INFO, 'Feed ' + request.POST['Go'].lower() + 'ed')
        elif request.POST['Go'] == 'Delete':
            f.delete()
            messages.add_message(request, messages.INFO, 'Feed deleted')
            return HttpResponseRedirect(reverse('feed_subscriptions'))

    else:
        form = FeedForm()  # An unbound form

    if feed_id:
        form = FeedForm(instance=f)
        subscribers = UserProfile.objects.filter(
            rss_feeds__contains=[feed_id]
        )
        if subscribers:
            subscribers = ', '.join([x.user.username for x in subscribers])

    return render(request, 'feed/edit.html',
                  {'section': SECTION,
                   'action': action,
                   'form': form,
                   'subscribers': subscribers,
                   'title': title})


@login_required
def check_url(request, url):

    url = urllib.parse.unquote(url)

    r = requests.get(url)
    if r.status_code != 200:
        status = {'status': r.status_code,
                  'error': r.text}
    else:
        d = feedparser.parse(r.text)
        status = {'status': r.status_code,
                  'entry_count': len(d.entries)}

    return HttpResponse(json.dumps(status), content_type="application/json")
