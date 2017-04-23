import json
from solrpy.core import SolrConnection

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models.signals import post_save

from bookmark.tasks import index_bookmark
from lib.mixins import TimeStampedModel
from tag.models import Tag


# This custom field lets us use a checkbox on the form, which, if checked,
#  results in a blob of JSON stored in the database rather than
#  the usual boolean value.
class DailyBookmarkJSONField(JSONField):

    def to_python(self, value):
        print("value is {}".format(value))
        if value is True:
            return json.loads('{"viewed": "false"}')
        else:
            return None


class Bookmark(TimeStampedModel):
    url = models.TextField()
    title = models.TextField()
    user = models.ForeignKey(User)
    note = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)
    is_pinned = models.BooleanField(default=False)
    daily = DailyBookmarkJSONField(blank=True, null=True)
    last_check = models.DateTimeField(null=True)
    last_response_code = models.IntegerField(null=True)
    importance = models.IntegerField(default=1)

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def delete(self):
        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        conn.delete(queries=['id:bordercore_bookmark_%s' % (self.id)])
        conn.commit()

        super(Bookmark, self).delete()


def postSaveForBookmark(**kwargs):
    instance = kwargs.get('instance')
    index_bookmark.delay(instance.id)


post_save.connect(postSaveForBookmark, Bookmark)


class BookmarkTagUser(models.Model):
    tag = models.ForeignKey(Tag)
    user = models.ForeignKey(User)
    bookmark_list = ArrayField(models.IntegerField())
