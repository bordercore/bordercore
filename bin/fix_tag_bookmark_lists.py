#!/usr/bin/env python
# encoding: utf-8

import sys

from bookmark.models import Bookmark, BookmarkTagUser
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

sys.path.insert(0, "/home/jerrell/dev/django/bordercore")

me = User.objects.get(username='jerrell')

# Get all bookmarks which have been tagged
bookmarks = Bookmark.objects.select_related().filter(user=me, tags__name__isnull=False)

for bookmark in bookmarks:

    print bookmark.title

    # Get all tags for this bookmark
    for tag in bookmark.tags.all():
        print tag.name
        try:
            existing_sorted_list = BookmarkTagUser.objects.get(tag=tag, user=me)
        except ObjectDoesNotExist, e:
            print "tag: %s, adding bookmark %d to NEW sorted list" % (tag.name, bookmark.pk)
            existing_sorted_list = BookmarkTagUser(tag=tag, user=me, bookmark_list=[bookmark.pk])
            existing_sorted_list.save()

        if bookmark.pk not in existing_sorted_list.bookmark_list:
            print "tag: %s, adding bookmark %d to the sorted list" % (tag.name, bookmark.pk)
            existing_sorted_list.bookmark_list.append(bookmark.pk)
            existing_sorted_list.save()


