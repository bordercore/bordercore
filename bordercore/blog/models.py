from django.contrib.auth.models import User
from django.db import models
import markdown

from lib.mixins import TimeStampedModel
from tag.models import Tag


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


class Post(TimeStampedModel):
    post = models.TextField()
    title = models.TextField(null=True)
    date = models.DateTimeField(editable=True)
    user = models.ForeignKey(User)
    blog = models.ForeignKey(Blog)
    tags = models.ManyToManyField(Tag)
#    reference = models.ForeignKey('self', related_name='reference_id', null=True, blank=True)

    def get_markdown(self):
        return markdown.markdown(self.post, extensions=['codehilite(guess_lang=False)'])

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

