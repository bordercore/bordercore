import string
from urllib.parse import unquote

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse

from lib.time_utils import convert_seconds
from lib.util import get_elasticsearch_connection

from .models import Album, Artist, Playlist, PlaylistItem

SEARCH_LIMIT = 1000


def get_playlist_counts(user):

    return Playlist.objects.filter(
        user=user
    ).annotate(
        num_songs=Count("playlistitem")
    ).order_by(
        "name"
    )


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
            "artist": x.song.artist.name,
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


def get_recent_albums(user, page_number=1):

    ALBUMS_PER_PAGE = 12

    query = Album.objects.filter(
        user=user
    ).select_related(
        "artist"
    ).order_by(
        "-created"
    )

    paginator = Paginator(query, ALBUMS_PER_PAGE)
    page = paginator.get_page(page_number)

    paginator_info = {
        "page_number": page_number,
        "has_next": page.has_next(),
        "has_previous": page.has_previous(),
        "next_page_number": page.next_page_number() if page.has_next() else None,
        "previous_page_number": page.previous_page_number() if page.has_previous() else None,
        "count": paginator.count
    }

    recent_albums = [
        {
            "uuid": x.uuid,
            "title": x.title,
            "artist_uuid": x.artist.uuid,
            "artist_name": x.artist.name,
            "created": x.created.strftime("%B %Y"),
            "album_url": reverse("music:album_detail", kwargs={"uuid": x.uuid}),
            "artwork_url": f"{settings.IMAGES_URL}album_artwork/{x.uuid}",
            "artist_url": reverse("music:artist_detail", kwargs={"artist_uuid": x.artist.uuid}),
        } for x in page.object_list
    ]

    return recent_albums, paginator_info


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


def get_unique_artist_letters(user):
    """
    Get a unique list of the first letter of every artist name
    """
    unique_letters = set()
    queryset = Artist.objects.filter(user=user) \
                             .filter(album__isnull=False) \
                             .distinct("name")

    for artist in queryset:
        first_letter = artist.name.lower()[0]
        if first_letter not in list(string.ascii_lowercase):
            unique_letters.add("other")
        else:
            unique_letters.add(first_letter)

    return unique_letters


def get_artist_counts(user, letter):
    """
    For all artists whose name starts with the specified letter,
    get their total song and album counts
    """
    album_counts = Artist.objects.filter(name__istartswith=letter) \
        .filter(user=user) \
        .filter(album__isnull=False) \
        .annotate(album_count=Count("album"))

    song_counts = Artist.objects.filter(name__istartswith=letter) \
        .filter(user=user) \
        .annotate(song_count=Count("song"))

    album_counts_dict = {}
    for artist in album_counts:
        album_counts_dict[str(artist.uuid)] = artist.album_count

    song_counts_dict = {}
    for artist in song_counts:
        song_counts_dict[str(artist.uuid)] = artist.song_count

    return {
        "album_counts": album_counts_dict,
        "song_counts": song_counts_dict
    }
