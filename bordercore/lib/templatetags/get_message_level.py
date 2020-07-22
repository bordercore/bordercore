#
# This template tag converts the Django message level as part of its
#  "Message tags" system to the equivalent Boostrap alert level.
#

from django import template

register = template.Library()


DJANGO_TO_BOOTSTRAP = {
    "debug": "info",
    "info": "info",
    "success": "success",
    "warning": "warning",
    "error": "danger"
}

DEFAULT_LEVEL = "info"


@register.filter(name="get_message_level")
def object_attrib(string):

    return DJANGO_TO_BOOTSTRAP.get(string, DEFAULT_LEVEL)
