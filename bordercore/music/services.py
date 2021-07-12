from django.db.models import Count

from .models import Playlist


def get_playlist_counts(user):

    # First get the song counts for all "smart" playlists from the "size" field
    playlist_sizes = {
        x["uuid"]: x["size"]
        for x
        in Playlist.objects.filter(user=user).values()
        if x["size"]
    }

    # Then get the song counts for all "manual" playlists from the "PlaylistItem" table
    playlists = Playlist.objects.filter(user=user).annotate(num_songs=Count("playlistitem"))

    # Finally, combine the two
    for p in playlists:
        if p.type != "manual":
            p.num_songs = playlist_sizes[p.uuid]
    return playlists
