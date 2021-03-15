import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

from .managers import MetricsManager


class Metric(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(blank=True, null=True)

    objects = MetricsManager()

    COVERAGE_MINIMUM = 80

    @staticmethod
    def get_failed_test_count(user):

        failed_test_count = 0

        latest_metrics = Metric.objects.latest_metrics(user)

        for metric in latest_metrics:

            if metric.created:

                if timezone.now() - metric.created > timedelta(days=1):
                    failed_test_count += 1
                if "test_errors" in metric.latest_result:
                    failed_test_count += int(metric.latest_result["test_errors"])
                if "test_failures" in metric.latest_result:
                    failed_test_count += int(metric.latest_result["test_failures"])

                if metric.name == "Bordercore Test Coverage":
                    line_rate = int(round(float(metric.latest_result["line_rate"]) * 100, 0))
                    if line_rate < Metric.COVERAGE_MINIMUM:
                        failed_test_count += 1

        return failed_test_count


class MetricData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE)
    value = JSONField(blank=True, null=True)
