import os

import django
from django.db.models import Count, Min, Max

django.setup()

from django.contrib.auth.models import User

from tag.models import TagBookmark, TagBookmarkSortOrder

from bookmark.models import Bookmark


def test_tag_bookmark_sort_order():
    """
    This test checks for three things for each tag - bookmark "sort order" relationship:

    min(sort_order) = 1
    max(sort_order) should equal the total count
    No duplicate sort_order values
    """
    for tag_bookmark in TagBookmark.objects.all():
        count = tag_bookmark.tagbookmarksortorder_set.count()
        if count > 0:
            assert TagBookmarkSortOrder.objects.filter(tag_bookmark=tag_bookmark).aggregate(Min('sort_order'))['sort_order__min'] == 1, "Min(sort_order) is not 1 for tag={}".format(tag_bookmark.tag.name)
            assert TagBookmarkSortOrder.objects.filter(tag_bookmark=tag_bookmark).aggregate(Max('sort_order'))['sort_order__max'] == count, "Max(sort_order) does not equal total count for tag={}".format(tag_bookmark.tag.name)

            q = TagBookmarkSortOrder.objects.values('sort_order', 'tag_bookmark').order_by().annotate(dcount=Count('sort_order')).filter(dcount__gt=1)
            assert len(q) == 0, "Multiple sort_order values found for tag={}".format(tag_bookmark.tag.name)


def test_tagbookmarksortorder_exists():
    """
    Every bookmark with a tag must have a representative
    TagBookmarkSortOrder object.
    """
    bookmarks = Bookmark.objects.filter(tags__isnull=False).distinct()

    for b in bookmarks:
        for tag in b.tags.all():
            if TagBookmarkSortOrder.objects.filter(bookmark=b, tag_bookmark__tag=tag).exists() is False:
                tb = TagBookmark.objects.get(tag=tag, user=b.user)
                tbso = TagBookmarkSortOrder(tag_bookmark=tb, bookmark=b)
                tbso.save()
            assert TagBookmarkSortOrder.objects.filter(bookmark=b, tag_bookmark__tag=tag).exists() == True, "bookmark={}, tag={}".format(b.id, tag.name)
