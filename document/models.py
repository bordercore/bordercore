from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
import markdown

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Document(TimeStampedModel):
    content = models.TextField()
    title = models.TextField(null=True)
    author = ArrayField(models.TextField(blank=True))
    source = models.TextField(null=True)
    pub_date = models.DateField(null=True)
    url = models.TextField(null=True)
    sub_heading = models.TextField(null=True)
    user = models.ForeignKey(User)
    note = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)

    def get_markdown(self):
        return markdown.markdown(self.content, extensions=['codehilite(guess_lang=False)'])

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])
