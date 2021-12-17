from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


doctype_mapping = {
    "album": "Albums",
    "blob": "Blobs",
    "book": "Books",
    "drill": "Drill",
    "note": "Notes",
    "bookmark": "Bookmarks",
    "todo": "Todo Items",
    "song": "Songs",
    "document": "Documents"
}


@register.filter(name="get_doctype")
@stringfilter
def object_attrib(value, doctype):
    return doctype_mapping[doctype]
