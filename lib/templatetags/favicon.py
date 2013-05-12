import re

from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='favicon')
def favicon(url):

    if not url:
        return

    p = re.compile("https?://(.*?)/")

    m = p.match(url)

    if m:
        domain = m.group(1)
        parts = domain.split('.')
        # We want the domain part of the hostname (eg npr.org instead of www.npr.org)
        if len(parts) == 3:
            domain = '.'.join(parts[1:])

    return """
<img src="%s/img/favicons/%s" />
""" % (settings.STATIC_URL, domain)
