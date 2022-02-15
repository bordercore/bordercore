from django import template

from lib.time_utils import get_relative_date_from_date

register = template.Library()


@register.filter
def relative_date(date):
    return get_relative_date_from_date(date)
