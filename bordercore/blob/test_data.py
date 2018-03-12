import json
import os
import re

import django
from django.conf import settings
from django.db.models import Q

from solrpy.core import SolrConnection

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'

django.setup()

from blob.models import Document
from collection.models import Collection
from tag.models import Tag

blob_whitelist = ()

def test_books_with_tags():
    "Assert that all books have at least one tag"
    solr_args = {'q': 'doctype:book AND -tags:[* TO *]',
                 'fl': 'id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']['numFound']
    assert data == 0, "{} books fail this test".format(data)


def test_books_with_title():
    "Assert that all books have a title"
    solr_args = {'q': 'doctype:book AND -title:[* TO *]',
                 'fl': 'id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']['numFound']
    assert data == 0, "{} books fail this test".format(data)


def test_books_with_author():
    "Assert that all books have at least one author"
    solr_args = {'q': 'doctype:book AND -author:[* TO *]',
                 'fl': 'id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']['numFound']
    assert data == 0, "{} books fail this test".format(data)


def test_tags_all_lowercase():
    "Assert that all tags are lowercase"
    t = Tag.objects.filter(name__regex=r'[[:upper:]]+')
    assert len(t) == 0, "{} tags fail this test".format(len(t))


def test_blobs_on_filesystem_exist_in_db():
    "Assert that all blobs found on the filesystem exist in the database"
    p = re.compile(settings.MEDIA_ROOT + '/\w\w/(\w{40})')

    for root, subdirs, files in os.walk(settings.MEDIA_ROOT):
        matches = p.match(root)
        if matches:
            assert Document.objects.filter(sha1sum=matches.group(1)).count() == 1, "blob {} exists on filesystem but not in database".format(matches.group(1))


def test_blobs_in_db_exist_in_solr():
    "Assert that all blobs in the database exist in Solr"

    blobs = Document.objects.all()

    for b in blobs:
        if str(b.uuid) in blob_whitelist:
            break
        solr_args = {'q': 'uuid:{}'.format(b.uuid),
                     'fl': 'id',
                     'wt': 'json'}

        conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response.decode('UTF-8'))['response']['numFound']
        assert data == 1, "blob found in the database but not in Solr, uuid={}".format(b.uuid)


def test_images_on_filesystem_have_thumbnails():
    "Assert that every image blob has a thumbnail"
    p = re.compile(settings.MEDIA_ROOT + '/\w\w/(\w{40})')

    images = Document.objects.filter(~Q(file=''))
    for blob in images:
        _, file_extension = os.path.splitext(str(blob.file))
        if blob.is_image():
            filename = "{}/{}/cover-small.jpg".format(settings.MEDIA_ROOT, os.path.dirname(blob.file.name))
            assert os.path.isfile(filename) is not False, "image blob {} does not have a thumbnail".format(blob.sha1sum)


def test_solr_blobs_exist_on_filesystem():
    "Assert that all blobs in Solr exist on the filesystem"
    solr_args = {'q': 'doctype:book OR doctype:blob',
                 'fl': 'filepath,sha1sum',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']
    for result in data['docs']:
        assert os.path.isfile(result['filepath']) is not False, "blob {} exists in Solr but not on the filesystem".format(result['sha1sum'])


def test_solr_blobs_exist_in_db():
    "Assert that all blobs in Solr exist in the database"
    solr_args = {'q': 'doctype:book OR doctype:blob OR doctype:document',
                 'fl': 'sha1sum,uuid,id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']
    for result in data['docs']:
        assert Document.objects.filter(uuid=result['uuid']).count() == 1, "blob {} exists in Solr but not in database".format(result['uuid'])


def test_blob_permissions():
    "Assert that all blobs are owned by www-data and all directories have permissions 775"
    import os
    from os import stat
    from pwd import getpwuid

    owners = ("celery", "www-data")
    walk_dir = "/home/media/blobs/"

    for root, subdirs, files in os.walk(walk_dir):
        for subdir in subdirs:
            dir_path = os.path.join(root, subdir)
            permissions = oct(stat(dir_path).st_mode & 0o777)
            assert permissions == "0o775", "directory is not 775 {}: {}".format(dir_path, permissions)
        for filename in files:
            file_path = os.path.join(root, filename)
            assert getpwuid(stat(file_path).st_uid).pw_name in owners, "file not owned by {}: {}".format(owners, file_path)


def test_collection_blobs_exists_in_db():
    "Assert that all blobs currently in collections actually exist in the database"
    collections = Collection.objects.filter(blob_list__isnull=False)

    for c in collections:
        for blob in c.blob_list:
            assert Document.objects.filter(pk=blob['id']).count() > 0, "blob_id {} does not exist in the database".format(blob['id'])


def test_collection_blobs_exists_in_solr():
    "Assert that all blobs currently in collections actually exist in Solr"
    collections = Collection.objects.filter(blob_list__isnull=False)

    for c in collections:
        for blob_info in c.blob_list:
            blob = Document.objects.get(pk=blob_info['id'])

            solr_args = {'q': 'uuid:{}'.format(blob.uuid),
                         'fl': 'id',
                         'wt': 'json'}

            conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
            response = conn.raw_query(**solr_args)
            data = json.loads(response.decode('UTF-8'))['response']['numFound']
            assert data == 1, "blob uuid={} does not exist in solr".format(blob.uuid)


def test_solr_search():
    "Assert that a simple Solr search works"

    solr_args = {'q': 'carl sagan',
                 'fl': 'id',
                 'rows': 1,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']['numFound']
    assert data >= 1, "solr search fails"
