from django import template

register = template.Library()


@register.filter(name="unescape_em")
def unescape_em(text):
    """
    Unescape all <em> tags, typically used to display highlighted
    search results by Elasticsearch, which by default surrounds matched
    terms in <em> tags.
    """
    return text.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
