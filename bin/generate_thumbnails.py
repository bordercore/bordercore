#!/usr/bin/env python
# encoding: utf-8

import os

import django
from django.db.models import Q

django.setup()

from blob.models import Document
from blob.tasks import create_thumbnail

images = Document.objects.filter(~Q(file=''))
for blob in images:
    _, file_extension = os.path.splitext(str(blob.file))
    if blob.is_image():
        print("file: {}".format(blob.file))
        create_thumbnail.delay(blob.uuid)
