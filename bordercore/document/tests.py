import django
import json
import os
from solrpy.core import SolrConnection
import sys

from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'bordercore.config.settings.prod'
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore')
sys.path.insert(0, '/home/www/htdocs/bordercore-django/bordercore/bordercore')

django.setup()

from document.models import Document


def test_documents_in_db_exist_in_solr():
    "Assert that all documents in the database exist in Solr"
    blobs = Document.objects.all()

    for b in blobs:
        solr_args = {'q': 'id:bordercore_document_%s' % (b.id),
                     'fl': 'id',
                     'wt': 'json'}

        conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
        response = conn.raw_query(**solr_args)
        data = json.loads(response.decode('UTF-8'))['response']['numFound']
        assert data == 1, "document %s found in the database but not in Solr" % b.id


def test_solr_documents_exist_in_db():
    "Assert that all documents in Solr exist in the database"
    solr_args = {'q': 'doctype:document',
                 'fl': 'internal_id',
                 'rows': 2147483647,
                 'wt': 'json'}

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    response = conn.raw_query(**solr_args)
    data = json.loads(response.decode('UTF-8'))['response']
    for result in data['docs']:
        assert Document.objects.filter(id=result['internal_id']).count() == 1, "document %s exists in Solr but not in database" % result['internal_id']
