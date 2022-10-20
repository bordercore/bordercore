from django.core.cache import cache
from django.urls import reverse

from bookmark.models import Bookmark


def get_recent_bookmarks(user, limit=10):
    """
    Return a list of recently created bookmarks
    """

    if "recent_bookmarks" in cache:
        return cache.get("recent_bookmarks")

    bookmark_list = Bookmark.objects.filter(
        user=user
    ).order_by(
        "-created"
    )[:limit]

    returned_bookmark_list = []

    for bookmark in bookmark_list:

        bookmark_dict = {
            "name": bookmark.name,
            "url": reverse("blob:detail", kwargs={"uuid": bookmark.uuid}),
            "uuid": str(bookmark.uuid),
            "doctype": "Bookmark",
            "thumbnail_url": bookmark.thumbnail_url,
            "type": "bookmark"
        }

        returned_bookmark_list.append(bookmark_dict)

    cache.set("recent_bookmarks", returned_bookmark_list)

    return returned_bookmark_list
