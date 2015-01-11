from django.contrib.auth.models import User
from django.db import models
from lib.mixins import TimeStampedModel

from tag.models import Tag

class Blob(TimeStampedModel):
    """
    A blob belonging to a user.
    """
    sha1sum = models.CharField(max_length=40)
    file_path = models.TextField()
    user = models.ForeignKey(User)
    tags = models.ManyToManyField(Tag)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])


class MetaData(TimeStampedModel):
    name = models.TextField()
    value = models.TextField()
    blob = models.ForeignKey(Blob)

    class Meta:
        unique_together = ('name', 'value', 'blob')

