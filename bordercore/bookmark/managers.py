from django.apps import apps
from django.db import models


class BookmarkManager(models.Manager):

    def bare_bookmarks(self, user, limit=10, sort=True):
        """
        Return all untagged bookmarks not associated with other objects
        """
        Bookmark = apps.get_model("bookmark", "Bookmark")

        query = Bookmark.objects.filter(
            user=user,
            tags__isnull=True,
            sortorderquestionbookmark__isnull=True,
            collectionobject__isnull=True,
            sortorderblobbookmark__isnull=True,
        )

        if sort:
            query = query.order_by("-created")

        if limit:
            query = query[:limit]

        return query
