import http.client
from urllib.parse import unquote

import feedparser
import requests
from feed.models import Feed
from rest_framework.decorators import api_view

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from accounts.models import UserFeed


@method_decorator(login_required, name="dispatch")
class FeedListView(ListView):
    template_name = "feed/index.html"

    def get_queryset(self):
        return self.request.user.userprofile.feeds.all().order_by("userfeed__sort_order").prefetch_related("feeditem_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = "Feed List"

        context["feed_list"] = [
            {
                "id": feed.id,
                "uuid": feed.uuid,
                "name": feed.name,
                "lastCheck": feed.last_check.strftime("%b %d, %Y, %I:%M %p")
 if feed.last_check else "N/A",
                "lastResponse": http.client.responses[feed.last_response_code] if feed.last_response_code else None,
                "homepage": feed.homepage,
                "url": feed.url,
                "feedItems": [
                    {
                        "id": item.id,
                        "link": item.link,
                        "title": item.title,
                    }
                    for item in feed.feeditem_set.all()
                ]
            }
            for feed in self.object_list
        ]

        current_feed_id = Feed.get_current_feed_id(self.request.user, self.request.session)
        context["current_feed"] = [
            x
            for x in context["feed_list"]
            if x["id"] == current_feed_id
        ][0]

        return context


@login_required
def sort_feed(request):

    feed_id = int(request.POST["feed_id"])
    new_position = int(request.POST["position"])

    s = UserFeed.objects.get(userprofile=request.user.userprofile, feed__id=feed_id)
    UserFeed.reorder(s, new_position)

    return JsonResponse({"status": "OK"}, safe=False)


@api_view(["GET"])
def update_feed_list(request, feed_uuid):

    feed = Feed.objects.get(uuid=feed_uuid)
    updated_count = feed.update()
    status = {"status": "OK", "updated_count": updated_count}

    return JsonResponse(status, safe=False)


@login_required
def check_url(request, url):

    url = unquote(url)

    r = requests.get(url)
    if r.status_code != 200:
        status = {
            "status": "Error",
            "status_code": r.status_code,
            "error": r.text
        }
    else:
        d = feedparser.parse(r.text)
        status = {
            "status": "OK",
            "status_code": r.status_code,
            "entry_count": len(d.entries)
        }

    return JsonResponse(status, safe=False)
