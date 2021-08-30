from urllib.parse import urlparse

from django import template

register = template.Library()


@register.filter(name="domain")
def domain(url):
    return urlparse(url).netloc
