from urllib.parse import unquote

from django.conf import settings
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce

from lib.time_utils import convert_seconds
from lib.util import get_elasticsearch_connection

from .models import Playlist, PlaylistItem

SEARCH_LIMIT = 1000


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


def get_playlist_songs(playlist):

    playtime = PlaylistItem.objects.filter(
        playlist=playlist
    ).aggregate(
        total_time=Coalesce(Sum("song__length"), 0)
    )["total_time"]

    song_list = [
        {
            "playlistitem_uuid": x.uuid,
            "uuid": x.song.uuid,
            "sort_order": x.sort_order,
            "artist": x.song.artist,
            "title": x.song.title,
            "note": x.song.note,
            "year": x.song.year,
            "length": convert_seconds(x.song.length)
        }
        for x
        in PlaylistItem.objects.filter(playlist=playlist)
        .select_related("song").order_by("sort_order")
    ]

    return {
        "song_list": song_list,
        "playtime": playtime
    }


def search(user, artist_name):
    """
    Search for artists in Elasticsearch based on a substring.
    """

    es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

    search_term = unquote(artist_name.lower())

    search_object = {
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "user_id": user.id
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "match": {
                                        "artist.autocomplete": {
                                            "query": search_term,
                                            "operator": "and"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "aggs": {
            "distinct_artists": {
                "terms": {
                    "field": "artist.keyword",
                    "size": SEARCH_LIMIT
                }
            }
        },
        "from": 0,
        "size": 0,
        "_source": [""]
    }

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    return [
        {
            "artist": x["key"]
        }
        for x
        in
        results["aggregations"]["distinct_artists"]["buckets"]
    ]
