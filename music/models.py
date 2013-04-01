from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

from tag.models import Tag

class TimeStampedActivate(models.Model):
    created = models.DateTimeField(default=datetime.now)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True

class Album(TimeStampedActivate):
    title = models.TextField()
    artist = models.TextField()
    year = models.IntegerField()
    compilation = models.BooleanField(default=False)
    comment = models.TextField(null=True)

    class Meta:
        unique_together = ("title", "artist")

class SongSource(TimeStampedActivate):
    name = models.TextField()
    description = models.TextField()

    def __unicode__(self):
        return self.name

class Song(TimeStampedActivate):
    title = models.TextField()
    artist = models.TextField()
    album = models.ForeignKey(Album, null=True)
    track = models.IntegerField(null=True)
    year = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    comment = models.TextField(null=True)
    filename = models.TextField()
    source = models.ForeignKey(SongSource)
    times_played = models.IntegerField(default=0, null=True)
    original_album = models.TextField(null=True)
    original_year = models.IntegerField(null=True)
    tags = models.ManyToManyField(Tag)

class Listen(TimeStampedActivate):
    user = models.ForeignKey(User)
    song = models.ForeignKey(Song)
