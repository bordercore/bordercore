from django import template

register = template.Library()


@register.filter(name="escape_backticks")
def object_attrib(string):

    if string is None:
        return ""
    else:
        return string.replace("`", "\\`")
