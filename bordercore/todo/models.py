from solrpy.core import SolrConnection

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

from todo.tasks import index_todo
from lib.mixins import TimeStampedModel
from tag.models import Tag


class Todo(TimeStampedModel):
    task = models.TextField()
    note = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    due_date = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    is_urgent = models.BooleanField(default=False)

    def get_modified(self):
        return self.modified.strftime('%b %d, %Y')

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def delete(self):
        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        conn.delete(queries=['id:bordercore_todo_%s' % (self.id)])
        conn.commit()

        super(Todo, self).delete()


def postSaveForTodo(**kwargs):
    instance = kwargs.get('instance')
    index_todo.delay(instance.id)


post_save.connect(postSaveForTodo, Todo)
