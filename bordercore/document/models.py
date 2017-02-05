import solr

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.signals import post_save
import markdown

from document.tasks import index_document
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
    importance = models.IntegerField(default=1)

    def get_markdown(self):
        return markdown.markdown(self.content, extensions=['codehilite(guess_lang=False)'])

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def delete(self):
        conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        conn.delete(queries=['id:bordercore_document_%s' % (self.id)])
        conn.commit()

        super(Document, self).delete()


def postSaveForDocument(**kwargs):
    instance = kwargs.get('instance')
    index_document.delay(instance.id)


post_save.connect(postSaveForDocument, Document)
