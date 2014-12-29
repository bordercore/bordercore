
from django.contrib import admin

from blob.models import Blob
from blob.models import MetaData

admin.site.register(MetaData)
admin.site.register(Blob)
