from django import template

register = template.Library()


@register.filter(name="dict_get")
def object_attrib(dict, key):
    return dict.get(key)
