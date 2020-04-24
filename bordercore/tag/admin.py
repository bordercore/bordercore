from django.contrib import admin

from tag.models import Tag, TagAlias, TagBookmark, TagBookmarkSortOrder

admin.site.register(Tag)
admin.site.register(TagAlias)
admin.site.register(TagBookmark)
admin.site.register(TagBookmarkSortOrder)
