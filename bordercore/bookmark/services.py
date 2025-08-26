"""
Bookmark Services Module

This module provides service functions for handling bookmark-related operations
with caching support. It includes functions to retrieve recent bookmarks for users
with efficient caching strategies.

Functions:
    get_recent_bookmarks: Retrieve recently created bookmarks for a user with caching
"""

from typing import Any, Dict, List

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from bookmark.models import Bookmark


def get_recent_bookmarks(user: User, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Return a list of recently created bookmarks for a specific user.
    Results are cached per user to improve performance.

    Args:
        user: The user object to get bookmarks for
        limit: Maximum number of bookmarks to return (default: 10)

    Returns:
        List of bookmark dictionaries with name, url, uuid, doctype, thumbnail_url, and type
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
            "url": reverse("bookmark:update", kwargs={"uuid": bookmark.uuid}),
            "uuid": str(bookmark.uuid),
            "doctype": "Bookmark",
            "thumbnail_url": bookmark.thumbnail_url,
            "type": "bookmark"
        }

        returned_bookmark_list.append(bookmark_dict)

    cache.set("recent_bookmarks", returned_bookmark_list)

    return returned_bookmark_list
