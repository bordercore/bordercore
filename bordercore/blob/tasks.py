from __future__ import absolute_import

from celery import task
from subprocess import call

JAVA_HOME = '/opt/jdk1.8.0_73'
SOLRINDEXER_JAR = '/opt/lib/solrindexer.jar'


@task()
def index_blob(uuid):
    print("index blob: {}".format(uuid))
    cmd = "{}/bin/java -cp {} com.bordercore.solr.SolrIndexerDriver -u {}".format(JAVA_HOME, SOLRINDEXER_JAR, uuid)
    call(cmd.split())
