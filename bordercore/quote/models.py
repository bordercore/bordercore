import uuid

from django.contrib.auth.models import User
from django.db import models

from lib.mixins import TimeStampedModel


class Quote(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    quote = models.TextField()
    source = models.TextField()
    is_favorite = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.quote[:100]
