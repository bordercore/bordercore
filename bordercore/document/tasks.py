from celery import task
from solrpy.core import SolrConnection

from django.conf import settings


@task()
def index_document(id):

    # Import Django models here rather than globally at the top to avoid circular dependencies
    from document.models import Document
    document = Document.objects.get(pk=id)

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

    doc = dict(
        id="bordercore_document_%s" % document.id,
        internal_id=document.id,
        tags=[tag.name for tag in document.tags.all()],
        author=document.author,
        url=document.url,
        title=document.title,
        attr_content=document.content,
        subtitle=document.sub_heading,
        source=document.source,
        importance=document.importance,
        last_modified=document.modified,
        doctype='document'
    )
    conn.add(doc)
    conn.commit()
