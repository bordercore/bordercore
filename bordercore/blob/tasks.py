from __future__ import absolute_import
from celery import shared_task
import logging
import os
from subprocess import call

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename=os.environ['HOME'] + '/logs/solr-indexer.log',
                    filemode='a')

logger = logging.getLogger('bordercore.solrindexer')


@shared_task()
def index_document(sha1sum):

    logger.info("index document: %s" % (sha1sum))
    cmd = "java -jar /home/jerrell/dev/solr/solrindexer/build/libs/solrindexer.jar -s %s" % (sha1sum,)
    call(cmd.split())
