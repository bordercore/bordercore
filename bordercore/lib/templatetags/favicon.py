import re

from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='favicon')
def favicon(url, size=32):

    if not url:
        return ""

    p = re.compile("https?://([^/]*)")

    m = p.match(url)

    if m:
        domain = m.group(1)
        parts = domain.split('.')
        # We want the domain part of the hostname (eg npr.org instead of www.npr.org)
        if len(parts) == 3:
            domain = '.'.join(parts[1:])
        return """
<img src="%simg/favicons/%s.ico" width="%d" height="%d" />
""" % (settings.STATIC_URL, domain, size, size)
    else:
        return ""
