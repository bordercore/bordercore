from datetime import timedelta

from django.apps import apps
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone


class TodoManager(models.Manager):

    def priority_counts(self, user):
        """
        Return todo counts, grouped by priority.
        """

        Todo = apps.get_model("todo", "Todo")

        priority_counts = Todo.objects.values("priority") \
                                      .annotate(count=Count("priority")) \
                                      .filter(user=user) \
                                      .order_by("-count")

        cache = {}

        for x in priority_counts:
            cache[x["priority"]] = x["count"]

        filter_priority_options = [
            [1, "High", cache.get(1, 0)],
            [2, "Medium", cache.get(2, 0)],
            [3, "Low", cache.get(3, 0)]
        ]

        return filter_priority_options

    def created_counts(self, user):
        """
        Return todo counts, grouped by creation date.
        """

        Todo = apps.get_model("todo", "Todo")

        created_counts = Todo.objects.aggregate(
            last_day=Count('pk', filter=Q(created__gt=(timezone.now() - timedelta(days=int(1)))) & Q(user=user)),
            last_3_days=Count('pk', filter=Q(created__gt=(timezone.now() - timedelta(days=int(3)))) & Q(user=user)),
            last_week=Count('pk', filter=Q(created__gt=(timezone.now() - timedelta(days=int(7)))) & Q(user=user)),
            last_month=Count('pk', filter=Q(created__gt=(timezone.now() - timedelta(days=int(30)))) & Q(user=user))
        )

        filter_created_options = [
            ["1", "Last Day", created_counts.get("last_day", 0)],
            ["3", "Last 3 Days", created_counts.get("last_3_days", 0)],
            ["7", "Last Week", created_counts.get("last_week", 0)],
            ["30", "Last Month", created_counts.get("last_month", 0)],
        ]

        return filter_created_options
