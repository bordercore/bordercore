from django import template

from lib.util import favicon_url

register = template.Library()


@register.filter(name="favicon")
def favicon(url, size=32):

    return favicon_url(url, size)
