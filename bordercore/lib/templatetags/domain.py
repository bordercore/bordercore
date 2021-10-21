from urllib.parse import urlparse

from django import template

register = template.Library()


@register.filter(name="domain")
def domain(url):

    if not url:
        return ""

    return urlparse(url).netloc
