import django
import json
import os
from solrpy.core import SolrConnection

from django.db.models import Count
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'

django.setup()

from bookmark.models import Bookmark, TagBookmarkList


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


def test_bookmark_tags_match_solr():
    "Assert that all bookmarks tags match those found in Solr"
    blobs = Bookmark.objects.filter(tags__isnull=False)

    for b in blobs:
        tags = " AND ".join(["\"{}\"".format(x.name) for x in b.tags.all()])
        solr_args = {"q": "id:bordercore_bookmark_{} AND tags:({})".format(b.id, tags),
                     "fl": "id,tags",
                     "wt": "json"}

        conn = SolrConnection("http://{}:{}/{}".format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response.decode("UTF-8"))["response"]["numFound"]
        assert data == 1, "bookmark {} tags don't match those found in Solr".format(b.id)


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
    "Only one tag per user should be in represented by a TagBookmarkList"
    t = TagBookmarkList.objects.values('tag', 'user').order_by().annotate(user_count=Count('user')).filter(user_count__gt=1)
    assert len(t) == 0, "tags found more than once per user: {}".format(t)


def test_deleted_bookmarks_in_bookmarktaguser():
    "Check if every bookmark listed in each TagBookmarkList bookmark list exists"
    all = TagBookmarkList.objects.all()

    for x in all:
        bookmarks = Bookmark.objects.filter(id__in=x.bookmark_list)
        assert len(x.bookmark_list) == len(bookmarks), "Missing bookmark in TagBookmarkList {}".format(x.id)
