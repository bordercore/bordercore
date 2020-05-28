from django import template

register = template.Library()


@register.filter(name="is_in_group")
def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
