import django
import json
import os
from solrpy.core import SolrConnection

from django.db.models import Count
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'

django.setup()

from bookmark.models import Bookmark, BookmarkTagUser


def test_bookmarks_in_db_exist_in_solr():
    "Assert that all bookmarks in the database exist in Solr"
    blobs = Bookmark.objects.all()

    for b in blobs:
        solr_args = {'q': 'id:bordercore_bookmark_%s' % (b.id),
                     'fl': 'id',
                     'wt': 'json'}

        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response.decode('UTF-8'))['response']['numFound']
        assert data == 1, "bookmark %s found in the database but not in Solr" % b.id


def test_solr_bookmarks_exist_in_db():
    "Assert that all bookmarks in Solr exist in the database"
    solr_args = {'q': 'doctype:bordercore_bookmark',
                 'fl': 'internal_id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']
    for result in data['docs']:
        assert Bookmark.objects.filter(id=result['internal_id']).count() == 1, "bookmark %s exists in Solr but not in database" % result['internal_id']


def test_one_tag_per_user():
    "Only one tag per user should be in represented by a BookmarkTagUser"
    t = BookmarkTagUser.objects.values('tag', 'user').order_by().annotate(user_count=Count('user')).filter(user_count__gt=1)
    assert len(t) == 0, "tags found more than once per user: {}".format(t)
