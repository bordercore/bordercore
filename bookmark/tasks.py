import logging
import os.path
import re

from celery import task
from django.conf import settings
import requests

FAVICON_DIR = "%s/templates/static/%s" % (settings.PROJECT_ROOT, "img/favicons")

# Tell requests to not be so noisy
logging.getLogger("requests").setLevel(logging.WARNING)

@task()
def snarf_favicon(url, parse_domain=True):

    print "Snarfing favicon for %s" % url

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
            print "Can't parse domain from url"
            return

    else:
        domain = url

    # Verify that we don't already have it
    if os.path.isfile("%s/%s.ico" % (FAVICON_DIR, domain)):
        return

    r = requests.get('http://%s/favicon.ico' % domain)
    if r.status_code != 200:
        print "Error: status code for %s was %d" % (domain, r.status_code)
        return

    f = open("%s/%s.ico" % (FAVICON_DIR, domain), "wb")
    f.write(r.content)
    f.close()

