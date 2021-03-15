from django.apps import apps
from django.db import models
from django.db.models import OuterRef, Subquery


class MetricsManager(models.Manager):

    def latest_metrics(self, user):

        Metric = apps.get_model("metrics", "Metric")
        MetricData = apps.get_model("metrics", "MetricData")

        newest = MetricData.objects.filter(metric=OuterRef("pk")) \
                                   .order_by("-created")

        return Metric.objects.annotate(
            latest_result=Subquery(newest.values("value")[:1]),
            created=Subquery(newest.values("created")[:1])) \
            .filter(user=user)
