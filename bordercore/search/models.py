import uuid

from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import F

from lib.mixins import TimeStampedModel


class RecentSearch(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    search_text = models.TextField()
    sort_order = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    MAX_SIZE = 10

    def __str__(self):
        return self.search_text or ""

    @staticmethod
    def add(user, search_text):

        # Delete any previous rows containing this search text to avoid duplicates
        exists = RecentSearch.objects.filter(search_text=search_text).first()
        if exists:
            RecentSearch.objects.filter(search_text=search_text).delete()

            # Re-order all searches *after* the deleted one by reducing their sort_order by one
            RecentSearch.objects.filter(
                user=user,
                sort_order__gt=exists.sort_order
            ).update(
                sort_order=F("sort_order") - 1
            )

        with transaction.atomic():

            # Update the sort order so that the new search is first
            RecentSearch.objects.filter(
                user=user
            ).update(
                sort_order=F("sort_order") + 1
            )

            # Create the new search with default sort_order = 1
            obj = RecentSearch(user=user, search_text=search_text)
            obj.save()

        # Insure that only MAX_SIZE searches exist per user
        searches = RecentSearch.objects.filter(
            user=user
        ).only(
            "id"
        ).order_by(
            "-created"
        )[RecentSearch.MAX_SIZE:]

        if searches:
            RecentSearch.objects.filter(id__in=[x.id for x in searches]).delete()
