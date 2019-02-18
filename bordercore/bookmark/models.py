import json
from solrpy.core import SolrConnection

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ObjectDoesNotExist
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

        # Delete it from any bookmark_list in BookmarkTagUser
        bookmarktaguser = BookmarkTagUser.objects.filter(user=self.user, bookmark_list__contains=[self.id])
        for x in bookmarktaguser:
            x.bookmark_list.remove(self.id)
            x.save()

        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        conn.delete(queries=['id:bordercore_bookmark_%s' % (self.id)])
        conn.commit()

        super(Bookmark, self).delete()

    def update_bookmark_tags(self):
        """
        When a bookmark is edited, update all BookmarkTagUser objects
        to reflect this change.
        """

        # For existing bookmarks, check to see if the user is removing a tag.
        # If so, we need to remove it from the sorted list
        if self.pk is not None:
            for old_tag in self.tags.all():
                if old_tag.name not in [new_tag.name for new_tag in self.tags.all()]:
                    sorted_list = BookmarkTagUser.objects.get(tag=Tag.objects.get(name=old_tag.name), user=self.user)
                    sorted_list.bookmark_list.remove(self.id)
                    sorted_list.save()

        for new_tag in self.tags.all():
            # Has the user already used this tag with any bookmarks?
            try:
                sorted_list = TagBookmarkList.objects.get(tag=Tag.objects.get(name=new_tag.name), user=self.user)
                # Yes.  Now check if this bookmark already has this tag.
                if self.id not in sorted_list.bookmark_list:
                    # Nope.  So this bookmark goes to the top of the sorted list.
                    sorted_list.bookmark_list.insert(0, self.id)
                    sorted_list.save()
            except ObjectDoesNotExist:
                # This is the first time this tag has been applied to a bookmark.
                # Create a new list with one member (the current bookmark)
                sorted_list = BookmarkTagUser(tag=Tag.objects.get(name=new_tag.name),
                                              bookmark_list=[self.id],
                                              user=self.user)
                sorted_list.save()


def postSaveForBookmark(**kwargs):
    instance = kwargs.get('instance')
    instance.update_bookmark_tags()
    index_bookmark.delay(instance.id)


post_save.connect(postSaveForBookmark, Bookmark)


class BookmarkTagUser(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    bookmark_list = ArrayField(models.IntegerField())
