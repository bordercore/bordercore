import django
import json
import os
import solr
import sys

from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.config.settings.prod'
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore')
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore/bordercore')

django.setup()

from blog.models import Post


def test_blogposts_in_db_exist_in_solr():
    "Assert that all blog posts in the database exist in Solr"
    blog_posts = Post.objects.all()

    for b in blog_posts:
        solr_args = {'q': 'id:bordercore_blogpost_%s' % (b.id),
                     'fl': 'id',
                     'wt': 'json'}

        conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response)['response']['numFound']
        assert data == 1, "blogpost %s found in the database but not in Solr" % b.id


def test_solr_blogposts_exist_in_db():
    "Assert that all blog posts in Solr exist in the database"
    solr_args = {'q': 'doctype:bordercore_blogpost',
                 'fl': 'internal_id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response)['response']
    for result in data['docs']:
        assert Post.objects.filter(id=result['internal_id']).count() == 1, "blog post %s exists in Solr but not in database" % result['internal_id']
