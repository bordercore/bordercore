import uuid

import markdown

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Album(TimeStampedModel):
    title = models.TextField()
    artist = models.TextField()
    year = models.IntegerField()
    original_release_year = models.IntegerField(null=True)
    compilation = models.BooleanField(default=False)
    comment = models.TextField(null=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def get_comment(self):
        return markdown.markdown(self.comment, extensions=['codehilite(guess_lang=False)', 'tables'])

    class Meta:
        unique_together = ("title", "artist")


class SongSource(TimeStampedModel):
    name = models.TextField()
    description = models.TextField()

    def __unicode__(self):
        return self.name


class Song(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.TextField()
    artist = models.TextField()
    album = models.ForeignKey(Album, null=True, on_delete=models.PROTECT)
    track = models.IntegerField(null=True)
    year = models.IntegerField(null=True)
    length = models.IntegerField(blank=True, null=True)
    comment = models.TextField(null=True)
    source = models.ForeignKey(SongSource, on_delete=models.PROTECT)
    last_time_played = models.DateTimeField(null=True)
    times_played = models.IntegerField(default=0, blank=True, null=True)
    original_album = models.TextField(null=True)
    original_year = models.IntegerField(null=True)
    tags = models.ManyToManyField(Tag)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])


class Listen(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)


class WishList(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    song = models.TextField(null=True, blank=True)
    artist = models.TextField(null=True)
    album = models.TextField(null=True, blank=True)
    note = models.TextField(null=True)

    def get_created(self):
        return self.created.strftime('%b %d, %Y')

    def get_absolute_url(self):
        return reverse('wishlist_edit', args=[self.id])
