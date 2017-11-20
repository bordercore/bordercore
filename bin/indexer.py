#!/usr/bin/env python
# encoding: utf-8

import django
import getopt
import logging
import os
import sys

from solrpy.core import SolrConnection

from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'

django.setup()

from bookmark.models import Bookmark
from bookmark.tasks import index_bookmark

from todo.models import Todo
from todo.tasks import index_todo


def index_bookmarks_all():

    for b in Bookmark.objects.all():
        print(b.url)
        index_bookmark.delay(b.id, commit=False)


def index_todo_all():

    for t in Todo.objects.all():
        print(t.task)
        index_todo.delay(t.id, commit=False)


if __name__ == "__main__":

    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hbt", ["ifile=","ofile="])
    except getopt.GetoptError:
        print('indexer.py --help --bookmarks --todo')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '--help':
            print('indexer.py --help --bookmarks')
            sys.exit()
        elif opt in ("-b", "--bookmarks"):
            index_bookmarks_all()
        elif opt in ("-t", "--todo"):
            index_todo_all()
        else:
            print('indexer.py --help --bookmarks')
            sys.exit()

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    conn.commit()
