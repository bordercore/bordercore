from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

doctype_mapping = { 'bordercore_blog': 'Blog Entries',
                    'bordercore_bookmark': 'Bookmarks',
                    'bordercore_todo': 'Todo Items',
                    'document': 'Documents' }

@register.filter(name='get_doctype')
@stringfilter
def object_attrib(value, doctype):
    return doctype_mapping[doctype]
