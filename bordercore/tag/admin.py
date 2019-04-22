from django.contrib import admin

from tag.models import Tag, TagBookmark, TagBookmarkSortOrder

admin.site.register(Tag)
admin.site.register(TagBookmark)
admin.site.register(TagBookmarkSortOrder)
