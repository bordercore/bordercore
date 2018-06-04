from celery import task
import logging
import os.path
import re
import requests
from solrpy.core import SolrConnection

from django.conf import settings

FAVICON_DIR = "%s/static/%s" % (settings.PROJECT_DIR, "img/favicons")

# Tell requests to not be so noisy
logging.getLogger("requests").setLevel(logging.WARNING)


@task()
def snarf_favicon(url, parse_domain=True):

    logging.info("Snarfing favicon for %s" % url)

    if parse_domain:

        p = re.compile("https?://(.*?)/")
        m = p.match(url)

        if m:
            domain = m.group(1)
            parts = domain.split('.')
            # We want the domain part of the hostname (eg npr.org instead of www.npr.org)
            if len(parts) == 3:
                domain = '.'.join(parts[1:])
        else:
            logging.warn("Can't parse domain from url: %s" % url)
            return

    else:
        domain = url

    # Verify that we don't already have it
    if os.path.isfile("%s/%s.ico" % (FAVICON_DIR, domain)):
        return

    r = requests.get('http://%s/favicon.ico' % domain)
    if r.status_code != 200:
        logging.error("Error: status code for %s was %d" % (domain, r.status_code))
        return

    if len(r.content) == 0:
        logging.warn("favicon image size is zero for {}".format(domain))
        return

    f = open("%s/%s.ico" % (FAVICON_DIR, domain), "wb")
    f.write(r.content)
    f.close()


@task
def index_bookmark(id, commit=True):

    # Import Django models here rather than globally at the top to avoid circular dependencies
    from bookmark.models import Bookmark
    bookmark = Bookmark.objects.get(pk=id)

    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))

    doc = dict(
        id="bordercore_bookmark_%s" % bookmark.id,
        internal_id=bookmark.id,
        title=bookmark.title,
        bordercore_bookmark_note=bookmark.note,
        tags=[tag.name for tag in bookmark.tags.all()],
        url=bookmark.url,
        note=bookmark.note,
        importance=bookmark.importance,
        last_modified=bookmark.modified,
        doctype='bordercore_bookmark',
        date=bookmark.created,
        date_unixtime=bookmark.created.strftime("%s")
    )
    conn.add(doc)

    if commit:
        conn.commit()
