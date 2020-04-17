#!/usr/bin/env python
# encoding: utf-8

import getopt
import logging
import sys

from elasticsearch import Elasticsearch

import django
from django.conf import settings

django.setup()

from todo.models import Todo  # isort:skip
from bookmark.models import Bookmark  # isort:skip


def index_bookmarks_all(es):

    for b in Bookmark.objects.all():
        print(b.id)
        b.index_bookmark(es)


def index_todo_all(es):

    for t in Todo.objects.all():
        print(t.task)
        t.index_todo(es)


if __name__ == "__main__":

    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hbt", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('indexer.py --help --bookmarks --todo')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '--help':
            print('indexer.py --help --bookmarks')
            sys.exit()
        elif opt in ("-b", "--bookmarks"):
            index_bookmarks_all(es)
        elif opt in ("-t", "--todo"):
            index_todo_all(es)
        else:
            print('indexer.py --help --bookmarks --todo')
            sys.exit()
