import markdown
import solr

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

from blog.tasks import index_blog
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

    def delete(self):
        conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        conn.delete(queries=['id:bordercore_blogpost_%s' % (self.id)])
        conn.commit()

        super(Post, self).delete()


def postSaveForBlogPost(**kwargs):
    instance = kwargs.get('instance')
    index_blog.delay(instance.id)


post_save.connect(postSaveForBlogPost, Post)
