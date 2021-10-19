from django.apps import apps
from django.db import models


class BookmarkManager(models.Manager):

    def bare_bookmarks(self, user, limit=10):
        """
        Return all untagged bookmarks not associated with other objects
        """
        Bookmark = apps.get_model("bookmark", "Bookmark")

        return Bookmark.objects.filter(
            user=user,
            tags__isnull=True,
            sortorderdrillbookmark__isnull=True
        ).order_by("-created")[:limit]
