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

from accounts.models import SortOrderUserFeed
from feed.forms import FeedForm
from feed.models import Feed


@method_decorator(login_required, name="dispatch")
class FeedListView(ListView):
    template_name = "feed/index.html"

    def get_queryset(self):
        return self.request.user.userprofile.feeds.all().order_by("sortorderuserfeed__sort_order").prefetch_related("feeditem_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_feed = Feed.get_current_feed(self.request.user, self.request.session)

        context["current_feed"] = json.dumps(current_feed, default=str)
        context["title"] = "Feed List"
        context["no_left_block"] = True
        context["content_block_width"] = 12

        return context


@login_required
def sort_feed(request):

    feed_id = int(request.POST["feed_id"])
    new_position = int(request.POST["position"])

    s = SortOrderUserFeed.objects.get(userprofile=request.user.userprofile, feed__id=feed_id)
    SortOrderUserFeed.reorder(s, new_position)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def feed_update(request, feed_uuid=None):

    feed = None

    if feed_uuid:
        feed = Feed.objects.get(uuid=feed_uuid)
        action = "Update"
        title = f"Feed Update :: {feed.name}"
    else:
        action = "Create"
        title = "Feed Create"

    if request.method == "POST":
        if request.POST["Go"] in ["Update", "Create"]:
            form = FeedForm(request.POST, instance=feed)
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m()

                if request.POST["Go"] == "Create":
                    so = SortOrderUserFeed(userprofile=request.user.userprofile, feed=form.instance)
                    so.save()

                messages.add_message(request, messages.INFO, "Feed " + request.POST["Go"].lower() + "ed")
                return HttpResponseRedirect(reverse("feed:list"))

        elif request.POST["Go"] == "Delete":

            # If we're deleting the user's currently viewed feed, delete that from the session
            current_feed = request.session.get("current_feed")
            if current_feed and int(current_feed) == feed.id:
                request.session.pop("current_feed")

            feed.delete()
            messages.add_message(request, messages.INFO, "Feed deleted")
            return HttpResponseRedirect(reverse("feed:list"))

    else:
        form = FeedForm()

    if feed_uuid:
        form = FeedForm(instance=feed)

    return render(request, "feed/update.html",
                  {"action": action,
                   "form": form,
                   "title": title})


@login_required
def check_url(request, url):

    url = urllib.parse.unquote(url)

    r = requests.get(url)
    if r.status_code != 200:
        status = {"status": r.status_code,
                  "error": r.text}
    else:
        d = feedparser.parse(r.text)
        status = {"status": r.status_code,
                  "entry_count": len(d.entries)}

    return JsonResponse(status, safe=False)
