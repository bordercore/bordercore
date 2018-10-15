from django.contrib.auth.models import User
from django.db import models

from lib.mixins import TimeStampedModel


class Author(TimeStampedModel):
    name = models.TextField()


class Book(TimeStampedModel):
    title = models.TextField()
    author = models.ManyToManyField(Author)
    subtitle = models.TextField(null=True)
    isbn = models.TextField(null=True)
    asin = models.TextField(null=True)
    year = models.IntegerField(null=True)
    publisher = models.TextField(null=True)
    notes = models.TextField(null=True)
    own = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
