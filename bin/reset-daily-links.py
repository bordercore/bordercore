#!/usr/bin/env python
# encoding: utf-8

import os
import sys

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.config.settings.prod'
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore')
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore/bordercore')

django.setup()

from bookmark.models import Bookmark

daily_bookmarks = Bookmark.objects.filter(daily__isnull=False)
for bookmark in daily_bookmarks:
    bookmark.daily['viewed'] = 'false'
    bookmark.save()
