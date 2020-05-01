from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


doctype_mapping = {'blob': 'Blobs',
                   'book': 'Books',
                   'note': 'Notes',
                   'bordercore_bookmark': 'Bookmarks',
                   'todo': 'Todo Items',
                   'document': 'Documents'}


@register.filter(name='get_doctype')
@stringfilter
def object_attrib(value, doctype):
    return doctype_mapping[doctype]
