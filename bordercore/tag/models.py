from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import F


class Tag(models.Model):
    name = models.TextField(unique=True)
    is_meta = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_meta_tags(user):
        tags = cache.get('meta_tags')
        if not tags:
            tags = Tag.objects.filter(document__user=user, is_meta=True)
            cache.set('meta_tags', tags)
        return [x.name for x in tags]


# Add the import here to avoid a circular dependency
#  between Tag and Bookmark
from bookmark.models import Bookmark


class TagBookmark(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    bookmarks = models.ManyToManyField(Bookmark, through='TagBookmarkSortOrder')


class TagBookmarkSortOrder(models.Model):
    tag_bookmark = models.ForeignKey(TagBookmark, on_delete=models.CASCADE)
    bookmark = models.ForeignKey(Bookmark, on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=1)
    note = models.TextField()

    def delete(self):

        # Get all tags below this one
        # Move them up by decreasing their sort order

        TagBookmarkSortOrder.objects.filter(
            tag_bookmark=self.tag_bookmark,
            sort_order__gte=self.sort_order,
        ).update(
            sort_order=F('sort_order') - 1
        )

        super(TagBookmarkSortOrder, self).delete()

    def save(self, *args, **kwargs):

        # Don't do this for new objects
        if self.pk is None:
            TagBookmarkSortOrder.objects.filter(
                tag_bookmark=self.tag_bookmark
            ).update(
                sort_order=F('sort_order') + 1
            )

        super(TagBookmarkSortOrder, self).save(*args, **kwargs)

    def reorder(self, new_position):
        """
        Move a given bookmark to a new position in a sorted list
        """

        if self.sort_order != new_position:

            with transaction.atomic():
                if self.sort_order > new_position:
                    # Move the tag up the list
                    # All tags between the old position and the new position
                    #  need to be re-ordered by increasing their sort order

                    TagBookmarkSortOrder.objects.filter(
                        tag_bookmark=self.tag_bookmark,
                        sort_order__gte=new_position,
                        sort_order__lte=self.sort_order
                    ).update(
                        sort_order=F('sort_order') + 1
                    )
                else:
                    # Move the tag down the list
                    # All tags between the old position and the new position
                    #  need to be re-ordered by decreasing their sort order

                    TagBookmarkSortOrder.objects.filter(
                        tag_bookmark=self.tag_bookmark,
                        sort_order__lte=new_position,
                        sort_order__gte=self.sort_order
                    ).update(
                        sort_order=F('sort_order') - 1
                    )

                # Finally, update the sort order for the tag in question
                self.sort_order = new_position
                self.save()

    class Meta:
        unique_together = (

            # For a given tag, avoid duplicate bookmarks
            ('tag_bookmark', 'bookmark'),

        )
        ordering = ('sort_order',)
