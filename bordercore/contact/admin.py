
from django.contrib import admin

from contact.models import Contact


def first_and_last_name(obj):

    if obj.preferred_name == 'first_name':
        preferred_name = obj.first_name
    elif obj.preferred_name == 'middle_name':
        preferred_name = obj.middle_name
    else:
        preferred_name = obj.last_name

    return ("{} {}".format(preferred_name, obj.last_name))


@admin.register(Contact)
class MyModelAdmin(admin.ModelAdmin):
    list_display = (first_and_last_name,)
