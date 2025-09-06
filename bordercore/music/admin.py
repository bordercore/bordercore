"""
Admin configuration for the music application.

This module customizes how models such as Album, Song, and SongSource
are displayed and managed in the Django admin interface. It defines
custom display functions and registers models with the admin site.
"""

from django.contrib import admin

from music.models import Album, Song, SongSource

admin.site.register(Song)
admin.site.register(SongSource)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    """Admin configuration for the Album model.

    Provides a custom list display that shows both the album title
    and the artist name for easier identification in the admin
    interface.
    """
    list_display = ("album_and_artist_names",)
    list_select_related = ("artist",)

    @admin.display(description="Album & Artist")
    def album_and_artist_names(self, obj: Album) -> str:
        """Return a formatted string with the album title and its artist.

        Args:
            obj (Album): The Album instance for which to display the name.

        Returns:
            str: A string in the format "<album title> by <artist name>".
        """
        return f"{obj.title} by {obj.artist}"
