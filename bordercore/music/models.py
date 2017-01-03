from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Album(TimeStampedModel):
    title = models.TextField()
    artist = models.TextField()
    year = models.IntegerField()
    compilation = models.BooleanField(default=False)
    comment = models.TextField(null=True)

    class Meta:
        unique_together = ("title", "artist")


class SongSource(TimeStampedModel):
    name = models.TextField()
    description = models.TextField()

    def __unicode__(self):
        return self.name


class Song(TimeStampedModel):
    title = models.TextField()
    artist = models.TextField()
    album = models.ForeignKey(Album, null=True)
    track = models.IntegerField(null=True)
    year = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    comment = models.TextField(null=True)
    source = models.ForeignKey(SongSource)
    last_time_played = models.DateTimeField(null=True)
    times_played = models.IntegerField(default=0, null=True)
    original_album = models.TextField(null=True)
    original_year = models.IntegerField(null=True)
    tags = models.ManyToManyField(Tag)


class Listen(TimeStampedModel):
    user = models.ForeignKey(User)
    song = models.ForeignKey(Song)


class WishList(TimeStampedModel):
    user = models.ForeignKey(User)
    song = models.TextField(null=True, blank=True)
    artist = models.TextField(null=True)
    album = models.TextField(null=True, blank=True)
    note = models.TextField(null=True)

    def get_created(self):
        return self.created.strftime('%b %d, %Y')

    def get_absolute_url(self):
        return reverse('wishlist_edit', args=[self.id])
