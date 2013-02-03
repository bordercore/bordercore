from django import template

register = template.Library()


#@register.simple_tag
@register.filter(name='object_attrib')
def object_attrib(object, attrib):
    return getattr(object, attrib)
