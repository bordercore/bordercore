from urllib.parse import urlparse

from django import template

register = template.Library()


@register.filter(name="favicon")
def favicon(url, size=32):

    if not url:
        return ""

    t = urlparse(url).netloc

    # We want the domain part of the hostname (eg bordercore.com instead of www.bordercore.com)
    domain = ".".join(t.split(".")[1:])

    return f"<img src=\"https://www.bordercore.com/favicons/{domain}.ico\" width=\"{size}\" height=\"{size}\" />"
