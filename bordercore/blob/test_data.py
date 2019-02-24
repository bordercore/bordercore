import json
import os
import re

import django
from django.conf import settings
from django.db.models import Count, Min, Max, Q

from solrpy.core import SolrConnection

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'

django.setup()

from django.contrib.auth.models import User

from accounts.models import SortOrder
from blob.models import Document, MetaData
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


def test_documents_with_dates():
    "Assert that all documents have a date"
    solr_args = {'q': 'doctype:document AND -date_unixtime:[* TO *]',
                 'fl': 'id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']['numFound']
    assert data == 0, "{} documents fail this test".format(data)


def test_dates_with_unixtimes():
    "Assert that all documents with dates also have a date_unixtime field"
    solr_args = {'q': 'doctype:blob AND -date_unixtime:[* TO *] AND date:[* TO *]',
                 'fl': 'id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']['numFound']
    assert data == 0, "{} documents fail this test".format(data)


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
                 'fl': 'id,uuid',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']
    assert data['numFound'] == 0, "{} books fail this test; example: uuid={}".format(data['numFound'], data['docs'][0]['uuid'])


def test_tags_all_lowercase():
    "Assert that all tags are lowercase"
    t = Tag.objects.filter(name__regex=r'[[:upper:]]+')
    assert len(t) == 0, "{} tags fail this test".format(len(t))


def test_tags_no_orphans():
    "Assert that all tags are used by some object"
    t = Tag.objects.filter(Q(todo__isnull=True) &
                           Q(document__isnull=True) &
                           Q(bookmark__isnull=True) &
                           Q(collection__isnull=True) &
                           Q(song__isnull=True) &
                           Q(tagbookmarklist__isnull=True))
    assert len(t) == 0, "{} tags fail this test; example: name={}".format(len(t), t[0].name)


def test_favorite_tags_sort_order():
    """
    This test checks for three things:

    For every user, min(sort_order) = 1
    For every user, max(sort_order) should equal the total count
    No duplicate sort_order values for each user
    """
    for user in User.objects.all():
        count = SortOrder.objects.filter(user_profile__user=user).count()
        if count > 0:
            assert SortOrder.objects.filter(user_profile__user=user).aggregate(Min('sort_order'))['sort_order__min'] == 1, "Min(sort_order) is not 1 for user={}".format(user)
            assert SortOrder.objects.filter(user_profile__user=user).aggregate(Max('sort_order'))['sort_order__max'] == count, "Max(sort_order) does not equal total count for user={}".format(user)

    q = SortOrder.objects.values('sort_order', 'user_profile_id').order_by().annotate(dcount=Count('sort_order')).filter(dcount__gt=1)
    assert len(q) == 0, "Multiple sort_order values found"


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
    solr_args = {'q': 'sha1sum:[* TO *]',
                 'fl': 'filepath,sha1sum',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']
    for result in data['docs']:
        assert os.path.isfile(result.get('filepath', '')) is not False, "blob {} exists in Solr but not on the filesystem".format(result['sha1sum'])


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


def test_blob_metadata_exists_in_solr():
    "Assert that blob metadata exists in Solr"
    metadata = MetaData.objects.all()

    defined_solr_fields = ('doctype', 'title', 'author', 'url')

    for m in metadata:
        name = m.name.replace(' ', '_').lower()
        if name == 'is_book':
            continue
        if name not in defined_solr_fields:
            name = 'attr_' + name
        # print('uuid:{} AND {}:"{}"'.format(m.blob.uuid, name, m.value.lower()))
        solr_args = {'q': 'uuid:{} AND {}:"{}"'.format(m.blob.uuid, name, m.value.lower().replace('"', '\\"')),
                     'fl': 'id',
                     'wt': 'json'}

        conn = SolrConnection('http://{}:{}/{}'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response.decode('UTF-8'))['response']['numFound']
        assert data == 1, "metadata for blob uuid={} does not exist in solr, {}:{}".format(m.blob.uuid, m.name, m.value)


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


def test_blob_tags_match_solr():
    "Assert that all blob tags match those found in Solr"
    blobs = Document.objects.filter(tags__isnull=False)

    for b in blobs:
        tags = " AND ".join(["\"{}\"".format(x.name) for x in b.tags.all()])
        solr_args = {"q": "uuid:{} AND tags:({})".format(b.uuid, tags),
                     "fl": "id,tags",
                     "wt": "json"}

        conn = SolrConnection("http://{}:{}/{}".format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response.decode("UTF-8"))["response"]["numFound"]
        assert data == 1, "blob uuid={} has tags which don't match those found in Solr".format(b.uuid)
