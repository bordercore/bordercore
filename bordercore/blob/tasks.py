from __future__ import absolute_import

import os.path
from subprocess import call

from django.conf import settings
from PIL import Image
import requests

from celery import task

JAVA_HOME = '/opt/jdk1.8.0_73'

SOLRINDEXER_JAR = '/opt/lib/solrindexer.jar'


@task()
def index_blob(uuid, file_changed):
    print("index blob: {}".format(uuid))
    cmd = "{}/bin/java -cp {} com.bordercore.solr.SolrIndexerDriver -u {} {}".format(JAVA_HOME, SOLRINDEXER_JAR, uuid, "--skip-indexing-file" if not file_changed else "")
    call(cmd.split())


@task()
def create_thumbnail(uuid, page_number=1):

    from blob.models import Document
    b = Document.objects.get(uuid=uuid)
    b.create_thumbnail(page_number)


@task()
def delete_metadata(uuid, name, value):

    from blob.models import Document
    blob = Document.objects.get(uuid=uuid)

    url = 'http://{}:{}/{}/update?commit=true'.format(settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION)
    headers = {'Content-type': 'application/json'}

    # "Author" is stored in its own Solr field, so we need
    # to handle it separately.
    if name == 'Author':
        solr_field = 'author'
    else:
        solr_field = 'attr_{}'.format(name)

    data = [{'doctype': 'blob',
             'uuid': str(blob.uuid),
             'id': "blob_{}".format(blob.id),
             solr_field: {'remove': value}
             }]

    r = requests.post(url, headers=headers, json=data)
    if (r.status_code != requests.codes.ok):
        print("Error deleting metadata for blog uuid={}: {}".format(blob.uuid, r.text))
