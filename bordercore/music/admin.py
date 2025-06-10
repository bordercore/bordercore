from django.contrib import admin

from music.models import Album, Song, SongSource

admin.site.register(Song)
admin.site.register(SongSource)


def album_and_artist_names(obj):
    return f"{obj.title} by {obj.artist}"


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = (album_and_artist_names,)
