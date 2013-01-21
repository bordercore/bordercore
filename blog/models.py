from django.db import models
from django.contrib.auth.models import User
from datetime import *

from tag.models import Tag

class TimeStampedActivate(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Blog(models.Model):
    """
    A blog belonging to a user.

    >>> b = Blog()
    >>> b.name = 'Foo Blog'
    >>> b.user = User.objects.create(username='foo',password='test')
    >>> b.save()
    >>> print b
    Foo Blog
    >>> print b.user.username
    foo
    """
    name = models.TextField()
    user = models.ForeignKey(User)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Post(models.Model):
    post = models.TextField()
    title = models.TextField(null=True)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    blog = models.ForeignKey(Blog)
    tags = models.ManyToManyField(Tag)
#    reference = models.ForeignKey('self', related_name='reference_id', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

