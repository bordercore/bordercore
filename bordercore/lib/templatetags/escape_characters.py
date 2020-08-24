from django import template

register = template.Library()


@register.filter(name="escape_characters")
def object_attrib(string):
    """
    Escape backticks and backslashes
    """

    if string is None:
        return ""
    else:
        # Note: The order of these two replace() functions is important
        return string.replace("\\", "\\\\").replace("`", "\\`")
