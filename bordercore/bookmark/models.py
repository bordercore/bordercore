import json
from solrpy.core import SolrConnection

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import m2m_changed

from bookmark.tasks import index_bookmark, snarf_favicon
from lib.mixins import TimeStampedModel
from tag.models import Tag


# This custom field lets us use a checkbox on the form, which, if checked,
#  results in a blob of JSON stored in the database rather than
#  the usual boolean value.
class DailyBookmarkJSONField(JSONField):

    def to_python(self, value):
        if value is True:
            return json.loads('{"viewed": "false"}')
        else:
            return None


class Bookmark(TimeStampedModel):
    url = models.TextField()
    title = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
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

        # Put the imports here to avoid circular dependencies
        from tag.models import TagBookmarkSortOrder
        for x in TagBookmarkSortOrder.objects.filter(bookmark=self):
            x.delete()

        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        conn.delete(queries=['id:bordercore_bookmark_%s' % (self.id)])
        conn.commit()

        super(Bookmark, self).delete()

    def post_save_wrapper(self):
        """
        This should be called anytime a bookmark is added or updated.
        """

        # Index the bookmark in Solr
        index_bookmark.delay(self.id)

        # Grab its favicon
        snarf_favicon.delay(self.url)


def tags_changed(sender, **kwargs):

    # Put the imports here to avoid circular dependencies
    from tag.models import TagBookmark, TagBookmarkSortOrder

    if kwargs["action"] == "post_add":

        bookmark = kwargs["instance"]
        for tag_id in kwargs["pk_set"]:

            try:
                tb = TagBookmark.objects.get(tag_id=tag_id, user=bookmark.user)
            except ObjectDoesNotExist:
                # If the tag is new, create a new instance
                tb = TagBookmark(tag_id=tag_id, user=bookmark.user)
                tb.save()

            tbso = TagBookmarkSortOrder(tag_bookmark=tb, bookmark=bookmark)
            tbso.save()

    elif kwargs["action"] == "post_remove":
        bookmark = kwargs["instance"]
        for tag_id in kwargs["pk_set"]:
            for x in TagBookmarkSortOrder.objects.filter(bookmark=bookmark).filter(tag_bookmark__tag__id=tag_id):
                x.delete()

m2m_changed.connect(tags_changed, sender=Bookmark.tags.through)
