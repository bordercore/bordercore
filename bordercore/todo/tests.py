import django
import json
import os
from solrpy.core import SolrConnection

from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'
django.setup()

from todo.models import Todo


def test_todo_tasks_in_db_exist_in_solr():
    "Assert that all todo tasks in the database exist in Solr"
    blobs = Todo.objects.all()

    for b in blobs:
        solr_args = {'q': 'id:bordercore_todo_%s' % (b.id),
                     'fl': 'id',
                     'wt': 'json'}

        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response.decode('UTF-8'))['response']['numFound']
        assert data == 1, "todo task %s found in the database but not in Solr" % b.id


def test_solr_todo_tasks_exist_in_db():
    "Assert that all todo tasks in Solr exist in the database"
    solr_args = {'q': 'doctype:bordercore_todo',
                 'fl': 'internal_id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']
    for result in data['docs']:
        assert Todo.objects.filter(id=result['internal_id']).count() == 1, "todo task %s exists in Solr but not in database" % result['internal_id']


def test_todo_tags_match_solr():
    "Assert that all todo tags match those found in Solr"
    blobs = Todo.objects.filter(tags__isnull=False)

    for b in blobs:
        tags = " AND ".join(["\"{}\"".format(x.name) for x in b.tags.all()])
        solr_args = {"q": "id:bordercore_todo_{} AND tags:({})".format(b.id, tags),
                     "fl": "id,tags",
                     "wt": "json"}

        conn = SolrConnection("http://{}:{}/{}".format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response.decode("UTF-8"))["response"]["numFound"]
        assert data == 1, "todo {} tags don't match those found in Solr".format(b.id)
