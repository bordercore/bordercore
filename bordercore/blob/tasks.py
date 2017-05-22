from __future__ import absolute_import

from celery import task
from subprocess import call

JAVA_HOME = '/opt/jdk1.8.0_73'
SOLRINDEXER_JAR = '/opt/lib/solrindexer.jar'


@task()
def index_blob(sha1sum):
    print("index blob: %s" % (sha1sum))
    cmd = "{}/bin/java -cp {} com.bordercore.solr.SolrIndexerDriver -s {}".format(JAVA_HOME, SOLRINDEXER_JAR, sha1sum)
    call(cmd.split())
