#!/usr/bin/env python
# encoding: utf-8

import django

django.setup()

from bookmark.models import Bookmark

daily_bookmarks = Bookmark.objects.filter(daily__isnull=False)
for bookmark in daily_bookmarks:
    bookmark.daily['viewed'] = 'false'
    bookmark.save()
