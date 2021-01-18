import uuid

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models

# class MetricGroup(models.Model):
#     uuid = models.UUIDField(default=uuid.uuid4, editable=False)


class Metric(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(blank=True, null=True)


class MetricData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE)
    value = JSONField(blank=True, null=True)
