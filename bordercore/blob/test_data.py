import django
import json
import os
import re
import solr
import sys

from django.db.models import Count, Q
from django.conf import settings
# from django.test import TestCase

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.config.settings.prod'
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore')
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore/bordercore')

django.setup()

from blob.models import Blob
from bookshelf.models import Bookshelf
from document.models import Document
from tag.models import Tag


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


def test_blobs_on_filesystem_exist_in_db():
    "Assert that all blobs found on the filesystem exist in the database"
    p = re.compile('%s/\w\w/(\w{40})' % Blob.BLOB_STORE)

    for root, subdirs, files in os.walk(Blob.BLOB_STORE):
        matches = p.match(root)
        if matches:
            assert Blob.objects.filter(sha1sum=matches.group(1)).count() == 1, "blob %s exists on filesystem but not in database" % matches.group(1)


def test_blobs_in_db_exist_in_solr():
    "Assert that all blobs in the database exist in Solr"
    blobs = Blob.objects.all()

    for b in blobs:
        if b.sha1sum in ['e5bd032709cc5aa2a0be50c6eeb19be788f8b404',
                         'f01176a1dbcf335159d78792a8b5f20746d3b12f',
                         '076d6870f5ee0626817a38b65c28b60c61e1628d']:
            continue
        solr_args = {'q': 'sha1sum:%s' % b.sha1sum,
                     'fl': 'id',
                     'wt': 'json'}

        conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response)['response']['numFound']
        assert data == 1, "blob %s found in the database but not in Solr" % b.sha1sum


def test_solr_blobs_exist_on_filesystem():
    "Assert that all blobs in Solr exist on the filesystem"
    solr_args = {'q': 'doctype:book OR doctype:blob',
                 'fl': 'sha1sum',
                 'wt': 'json'}

    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response)['response']
    for result in data['docs']:
        assert os.listdir("%s/%s/%s/" % (Blob.BLOB_STORE, result['sha1sum'][:2], result['sha1sum'])) != [], "blob %s exists in Solr but not on the filesystem" % result['sha1sum']


def test_solr_blobs_exist_in_db():
    "Assert that all blobs in Solr exist in the database"
    solr_args = {'q': 'doctype:book OR doctype:blob',
                 'fl': 'sha1sum',
                 'wt': 'json'}

    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response)['response']
    for result in data['docs']:
        assert Blob.objects.filter(sha1sum=result['sha1sum']).count() == 1, "blob %s exists in Solr but not in database" % result['sha1sum']


def test_blob_permissions():
    "Assert that all blobs are owned by www-data"
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


def test_documents_with_author():
    "Assert that all documents have at least one author"
    assert Document.objects.filter(Q(author__len=0) | Q(author__0_1=[''])).count() == 0
