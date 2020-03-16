from django import template

register = template.Library()

# A column titled "question_count" would
#  become "Question Count"
@register.filter(name="title_custom")
def object_attrib(name):
    return name.title().replace("_", " ")
