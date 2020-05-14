from django.contrib import admin

from music.models import Album, Listen, Song, SongSource

admin.site.register(Listen)
admin.site.register(Song)
admin.site.register(SongSource)

def album_and_artist_names(obj):
    return ("{} by {}".format(obj.title, obj.artist))

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = (album_and_artist_names,)
