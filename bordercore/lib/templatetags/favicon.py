import re

from django import template

register = template.Library()


@register.filter(name="favicon")
def favicon(url, size=32):

    if not url:
        return ""

    p = re.compile("https?://([^/]*)")

    m = p.match(url)

    if m:
        domain = m.group(1)
        parts = domain.split(".")
        # We want the domain part of the hostname (eg npr.org instead of www.npr.org)
        if len(parts) == 3:
            domain = ".".join(parts[1:])
        return f"<img src=\"https://www.bordercore.com/favicons/{domain}.ico\" width=\"{size}\" height=\"{size}\" />"
    else:
        return ""
