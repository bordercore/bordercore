from datetime import datetime

from django.db import models


class Tag(models.Model):
    name = models.TextField(unique=True)
    created = models.DateTimeField(default=datetime.now())
