from celery import task
import solr

from django.conf import settings


@task()
def index_blog(id):

    # Import Django models here rather than globally at the top to avoid circular dependencies
    from blog.models import Post
    blog = Post.objects.get(pk=id)

    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

    doc = dict(
        id="bordercore_blogpost_%s" % blog.id,
        internal_id=blog.id,
        bordercore_blogpost_title=blog.title,
        attr_content=blog.post,
        tags=[tag.name for tag in blog.tags.all()],
        last_modified=blog.modified,
        doctype='bordercore_blog'
    )
    conn.add(doc)
    conn.commit()
