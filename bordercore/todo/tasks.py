from celery import task
from solrpy.core import SolrConnection

from django.conf import settings


@task()
def index_todo(id):

    # Import Django models here rather than globally at the top to avoid circular dependencies
    from todo.models import Todo
    todo = Todo.objects.get(pk=id)

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

    doc = dict(
        id="bordercore_todo_%s" % todo.id,
        internal_id=todo.id,
        bordercore_todo_task=todo.task,
        tags=[tag.name for tag in todo.tags.all()],
        url=todo.url,
        note=todo.note,
        last_modified=todo.modified,
        doctype='bordercore_todo'
    )
    conn.add(doc)
    conn.commit()
