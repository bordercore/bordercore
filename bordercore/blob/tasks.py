from __future__ import absolute_import

import os.path
from subprocess import call

from django.conf import settings
from PIL import Image

from celery import task

JAVA_HOME = '/opt/jdk1.8.0_73'
SOLRINDEXER_JAR = '/opt/lib/solrindexer.jar'


@task()
def index_blob(uuid):
    print("index blob: {}".format(uuid))
    cmd = "{}/bin/java -cp {} com.bordercore.solr.SolrIndexerDriver -u {}".format(JAVA_HOME, SOLRINDEXER_JAR, uuid)
    call(cmd.split())


@task()
def create_thumbnail(uuid):

    print("create thumbnail for blob: {}".format(uuid))
    size = 128, 128

    from blob.models import Document
    b = Document.objects.get(uuid=uuid)
    if b.is_image():
        infile = "{}/{}".format(settings.MEDIA_ROOT, b.file.name)
        outfile = "{}/{}/cover-small.jpg".format(settings.MEDIA_ROOT, os.path.dirname(b.file.name))
        try:
            # Convert images to RGB mode to avoid "cannot write mode P as JPEG" errors for PNGs
            im = Image.open(infile).convert('RGB')
            im.thumbnail(size)
            im.save(outfile)
            os.chmod(outfile, 0o664)
        except IOError as err:
            print("cannot create thumbnail; error={}".format(err))
