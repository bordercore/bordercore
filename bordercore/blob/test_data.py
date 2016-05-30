import django
import json
import os
import solr
import sys

from django.db.models import Count
from django.conf import settings
# from django.test import TestCase

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.config.settings.prod'
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore')
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore/bordercore')

django.setup()

from blob.models import Blob
from bookshelf.models import Bookshelf
from tag.models import Tag

# t = Tag.objects.filter(name='linux')
# print t[0].name

# class DataQualityTests(TestCase):

#     def setUp(self):
#         os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.settings'
#         sys.path.insert(0, '/home/jerrell/dev/django')
#         sys.path.insert(0, '/home/jerrell/dev/django/bordercore')
#         self.conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

#     def test_books_with_tags(self):

#         solr_args = {'q': 'doctype:book AND -tags:[* TO *]',
#                      'fl': 'id',
#                      'wt': 'json'}

#         response = self.conn.raw_query(**solr_args)
#         data = json.loads(response)['response']['numFound']
#         self.assertEquals(data, 0)


def test_books_with_tags():
    "Assert that all books have at least one tag"
    solr_args = {'q': 'doctype:book AND -tags:[* TO *]',
                 'fl': 'id',
                 'wt': 'json'}

    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response)['response']['numFound']
    assert data == 0, "%s books fail this test" % data


def test_books_with_title():
    "Assert that all books have a title"
    solr_args = {'q': 'doctype:book AND -title:[* TO *]',
                 'fl': 'id',
                 'wt': 'json'}

    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response)['response']['numFound']
    assert data == 0, "%s books fail this test" % data


def test_books_with_author():
    "Assert that all books have at least one author"
    solr_args = {'q': 'doctype:book AND -author:[* TO *]',
                 'fl': 'id',
                 'wt': 'json'}

    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response)['response']['numFound']
    assert data == 0, "%s books fail this test" % data


def test_tags_all_lowercase():
    "Assert that all tags are lowercase"
    t = Tag.objects.filter(name__regex=r'[[:upper:]]+')
    assert len(t) == 0, "%s tags fail this test" % len(t)


# I'm not sure I need this test, as there could be legitimate reasons this test might fail
def test_blobs_with_duplicate_filenames():
    "Assert that all blobs have unique filenames"
    t = Blob.objects.values('filename').order_by().annotate(dcount=Count('sha1sum')).filter(dcount__gt=1)
    assert len(t) == 0, "%s tags fail this test" % len(t)


def test_blob_permissions():
    "Alert that all blobs are owned by www-data"
    import os
    from os import stat
    from pwd import getpwuid

    owner = "www-data"
    walk_dir = "/home/media/blobs/"

    for root, subdirs, files in os.walk(walk_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            assert getpwuid(stat(file_path).st_uid).pw_name == owner, "file not owned by %s: %s" % (owner, file_path)
#            print "%s, %s" % (file_path, getpwuid(stat(file_path).st_uid).pw_name)


def test_bookshelf_books_exists_in_db():
    "Assert that all books currently on bookshelves actually exist in the database"
    book_shelves = Bookshelf.objects.filter(blob_list__isnull=False)

    for shelf in book_shelves:
        for blob in shelf.blob_list:
            assert Blob.objects.filter(pk=blob['id']).count() > 0, "blob_id %s does not exist in the database" % blob['id']


def test_bookshelf_books_exists_in_solr():
    "Assert that all books currently on bookshelves actually exist in Solr"
    book_shelves = Bookshelf.objects.filter(blob_list__isnull=False)

    for shelf in book_shelves:
        for blob in shelf.blob_list:
            solr_args = {'q': 'id:blob_%s' % blob['id'],
                         'fl': 'id',
                         'wt': 'json'}

            conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
            response = conn.raw_query(**solr_args)
            data = json.loads(response)['response']['numFound']
            assert data == 1, "blob_id %s does not exist in solr" % blob['id']
