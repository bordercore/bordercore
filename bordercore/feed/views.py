import json
import urllib

import feedparser
import requests

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from accounts.models import UserProfile
from feed.forms import FeedForm
from feed.models import Feed


@method_decorator(login_required, name='dispatch')
class FeedListView(ListView):
    template_name = 'feed/index.html'
    context_object_name = 'subscribed_feeds_list'

    def get_queryset(self):
        return Feed.get_feed_list(self.request.user.userprofile.rss_feeds)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        default_feed_id = Feed.objects.get(name='Hacker News').id
        current_feed = Feed.objects.values("id", "homepage", "last_check", "name").filter(pk=self.request.session.get('current_feed', default_feed_id))[0]

        context['current_feed'] = json.dumps(current_feed, default=str)
        context['title'] = 'Feed List'
        context['no_left_block'] = True
        context['content_block_width'] = 12

        return context


@method_decorator(login_required, name='dispatch')
class FeedSubscriptionListView(ListView):
    template_name = 'feed/subscriptions.html'
    context_object_name = 'feed_info'

    def get_queryset(self):
        return Feed.get_feed_list(self.request.user.userprofile.rss_feeds, get_feed_items=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get a list of all feeds not currently subscribed to
        rss_feeds = self.request.user.userprofile.rss_feeds or []
        context['feeds_not_subscribed'] = sorted(
            Feed.objects.exclude(id__in=rss_feeds),
            key=lambda feed: feed.name.lower()
        )

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

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def feed_subscribe(request):

    feed_id = int(request.POST['feed_id'])
    position = int(request.POST['position'])

    feed = Feed.objects.get(pk=feed_id)
    feed.subscribe_user(request.user, position)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def feed_unsubscribe(request):

    feed_id = int(request.POST['feed_id'])

    feed = Feed.objects.get(pk=feed_id)
    feed.unsubscribe_user(request.user)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def feed_update(request, feed_uuid=None):

    f = None
    subscribers = None

    if feed_uuid:
        f = Feed.objects.get(uuid=feed_uuid)
        action = 'Update'
        title = 'Feed Update :: {}'.format(f.name)
    else:
        action = 'Create'
        title = 'Feed Create'

    if request.method == 'POST':
        if request.POST['Go'] in ['Update', 'Create']:
            form = FeedForm(request.POST, instance=f)
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m()

                if request.POST['Go'] == 'Create':
                    # If the user clicked the 'subscribe' checkbox, subscribe her
                    if request.POST.get('subscribe', ''):
                        newform.subscribe_user(request.user, 1)

                messages.add_message(request, messages.INFO, 'Feed ' + request.POST['Go'].lower() + 'ed')
        elif request.POST['Go'] == 'Delete':
            f.delete()
            messages.add_message(request, messages.INFO, 'Feed deleted')
            return HttpResponseRedirect(reverse('feed:subscriptions'))

    else:
        form = FeedForm()

    if feed_uuid:
        form = FeedForm(instance=f)
        subscribers = UserProfile.objects.filter(
            rss_feeds__contains=[f.id]
        )
        if subscribers:
            subscribers = ', '.join([x.user.username for x in subscribers])

    return render(request, 'feed/update.html',
                  {'action': action,
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

    return JsonResponse(status, safe=False)
