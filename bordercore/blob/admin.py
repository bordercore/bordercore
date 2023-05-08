from django.contrib import admin

from blob.models import Blob, BlobTemplate, MetaData

admin.site.register(Blob)
admin.site.register(BlobTemplate)
admin.site.register(MetaData)
