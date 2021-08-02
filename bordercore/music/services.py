from datetime import timedelta

from django.db.models import Count, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from lib.time_utils import convert_seconds

from .models import Listen, Playlist, PlaylistItem, Song


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


def get_playlist_songs_smart(playlist, size):

    if playlist.type == "tag":
        song_list = Song.objects.filter(tags__name=playlist.parameters["tag"])
    elif playlist.type == "time":
        song_list = Song.objects.filter(
            year__gte=playlist.parameters["start_year"],
            year__lte=playlist.parameters["end_year"],
        )
    else:
        raise ValueError(f"Playlist type not supported: {playlist.type}")

    if "exclude_albums" in playlist.parameters:
        song_list = song_list.exclude(album__isnull=False)

    if "exclude_recent" in playlist.parameters:

        latest = Listen.objects.filter(song=OuterRef("pk")).order_by("-created")

        song_list = song_list.annotate(
            latest_result=Subquery(latest.values("created")[:1])
        ).filter(
            Q(latest_result__isnull=True)
            | Q(latest_result__lte=timezone.now() - timedelta(days=int(playlist.parameters["exclude_recent"])))
        )

    if playlist.type == "recent":
        song_list = Song.objects.all().order_by("-created")
    else:
        song_list = song_list.order_by("?")

    if size:
        song_list = song_list[:size]

    playtime = 0
    for song in song_list:
        playtime += song.length

    song_list = [
        {
            "song_uuid": x.uuid,
            "sort_order": i,
            "artist": x.artist,
            "title": x.title,
            "note": x.note,
            "year": x.year,
            "length": convert_seconds(x.length)
        }
        for i, x
        in enumerate(song_list, 1)
    ]

    return {
        "song_list": song_list,
        "playtime": playtime
    }


def get_playlist_songs_manual(playlist):

    playtime = PlaylistItem.objects.filter(playlist=playlist).aggregate(total_time=Coalesce(Sum("song__length"), 0))["total_time"]

    song_list = [
        {
            "playlistitem_uuid": x.uuid,
            "song_uuid": x.song.uuid,
            "sort_order": x.sort_order,
            "artist": x.song.artist,
            "title": x.song.title,
            "note": x.song.note,
            "year": x.song.year,
            "length": convert_seconds(x.song.length)
        }
        for x
        in PlaylistItem.objects.filter(playlist=playlist)
        .select_related("song")
    ]

    return {
        "song_list": song_list,
        "playtime": playtime
    }
