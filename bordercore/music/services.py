"""Django services module for music application.

This module provides service functions for managing playlists, albums, artists,
and search functionality using Django ORM and Elasticsearch.
"""

import string
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import unquote

from elasticsearch import Elasticsearch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Page, Paginator
from django.db.models import Count, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse

from lib.time_utils import convert_seconds
from lib.util import get_elasticsearch_connection

from .models import Album, Artist, Playlist, PlaylistItem

SEARCH_LIMIT: int = 1000


def get_playlist_counts(user: User) -> QuerySet[Playlist]:
    """Get all playlists for a user with song counts.

    Retrieves all playlists belonging to the specified user, annotated with
    the number of songs in each playlist. Results are ordered alphabetically
    by playlist name.

    Args:
        user: The user to get playlists for.

    Returns:
        A QuerySet of Playlist objects annotated with 'num_songs' field
        containing the count of playlist items, ordered by name.
    """
    return Playlist.objects.filter(
        user=user
    ).annotate(
        num_songs=Count("playlistitem")
    ).order_by(
        "name"
    )


def get_playlist_songs(playlist: Playlist) -> Dict[str, Union[List[Dict[str, Any]], int]]:
    """Get all songs in a playlist with metadata and total playtime.

    Retrieves all songs in the specified playlist along with their metadata
    and calculates the total playtime for the entire playlist.

    Args:
        playlist: The Playlist instance to get songs for.

    Returns:
        A dictionary containing:
            - 'song_list': List of dictionaries with song metadata including:
                - playlistitem_uuid: UUID of the playlist item
                - uuid: UUID of the song
                - sort_order: Order of song in playlist
                - artist: Artist name
                - title: Song title
                - note: Song note/description
                - year: Release year
                - length: Formatted song length (e.g., "3:45")
            - 'playtime': Total playtime in seconds for all songs
    """
    playtime: int = PlaylistItem.objects.filter(
        playlist=playlist
    ).aggregate(
        total_time=Coalesce(Sum("song__length"), 0)
    )["total_time"]

    song_list: List[Dict[str, Any]] = [
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


def get_recent_albums(user: User, page_number: int = 1) -> Tuple[List[Dict[str, Any]], Dict[str, Union[int, bool, Optional[int]]]]:
    """Get paginated recent albums for a user.

    Retrieves the most recently created albums for a user with pagination
    support. Albums are ordered by creation date (newest first).

    Args:
        user: The user to get albums for.
        page_number: The page number to retrieve (1-indexed). Defaults to 1.

    Returns:
        A tuple containing:
            - List of album dictionaries with metadata including:
                - uuid: Album UUID
                - title: Album title
                - artist_uuid: Artist UUID
                - artist_name: Artist name
                - created: Formatted creation date (e.g., "January 2024")
                - album_url: URL to album detail page
                - artwork_url: URL to album artwork image
                - artist_url: URL to artist detail page
            - Pagination info dictionary with:
                - page_number: Current page number
                - has_next: Whether there's a next page
                - has_previous: Whether there's a previous page
                - next_page_number: Next page number or None
                - previous_page_number: Previous page number or None
                - count: Total number of albums
    """
    albums_per_page: int = 12

    query: QuerySet[Album] = Album.objects.filter(
        user=user
    ).select_related(
        "artist"
    ).order_by(
        "-created"
    )

    paginator: Paginator = Paginator(query, albums_per_page)
    page: Page = paginator.get_page(page_number)

    paginator_info: Dict[str, Union[int, bool, Optional[int]]] = {
        "page_number": page_number,
        "has_next": page.has_next(),
        "has_previous": page.has_previous(),
        "next_page_number": page.next_page_number() if page.has_next() else None,
        "previous_page_number": page.previous_page_number() if page.has_previous() else None,
        "count": paginator.count
    }

    recent_albums: List[Dict[str, Any]] = [
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


def search(user: User, artist_name: str) -> List[Dict[str, str]]:
    """Search for artists using Elasticsearch.

    Searches for artists in Elasticsearch based on a substring match.
    The search is scoped to the specified user's music collection and
    uses autocomplete functionality for efficient matching.

    Args:
        user: The user to scope the search to.
        artist_name: The artist name or substring to search for.

    Returns:
        A list of dictionaries containing matching artists:
            - artist: The artist name

    Raises:
        ConnectionError: If Elasticsearch connection fails.
        RequestError: If the search query is malformed.
    """
    es: Elasticsearch = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

    search_term: str = unquote(artist_name.lower())

    search_object: Dict[str, Any] = {
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

    results: Dict[str, Any] = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    return [
        {
            "artist": x["key"]
        }
        for x
        in
        results["aggregations"]["distinct_artists"]["buckets"]
    ]


def get_unique_artist_letters(user: User) -> Set[str]:
    """Get unique first letters of all artist names for a user.

    Retrieves a set of unique first letters from all artist names in the
    user's music collection. Non-alphabetic characters are grouped under 'other'.
    Only includes artists that have at least one album.

    Args:
        user: The user to get artist letters for.

    Returns:
        A set of lowercase letters ('a'-'z') and 'other' for non-alphabetic
        first characters.

    Note:
        Artists without albums are excluded from the results to ensure
        only meaningful entries are included.
    """
    unique_letters: Set[str] = set()
    queryset: QuerySet[Artist] = Artist.objects.filter(user=user) \
                                               .filter(album__isnull=False) \
                                               .distinct("name")

    for artist in queryset:
        first_letter: str = artist.name.lower()[0]
        if first_letter not in list(string.ascii_lowercase):
            unique_letters.add("other")
        else:
            unique_letters.add(first_letter)

    return unique_letters


def get_artist_counts(user: User, letter: str) -> Dict[str, Dict[str, int]]:
    """Get album and song counts for artists starting with a specific letter.

    Retrieves count statistics for all artists whose names start with the
    specified letter. Provides both album and song counts per artist.

    Args:
        user: The user to get artist counts for.
        letter: The first letter to filter artists by (case-insensitive).

    Returns:
        A dictionary containing:
            - 'album_counts': Dict mapping artist UUID strings to album counts
            - 'song_counts': Dict mapping artist UUID strings to song counts

    Note:
        Only artists with albums are included in album_counts, while
        song_counts includes all artists with songs regardless of albums.
    """
    album_counts: QuerySet[Artist] = Artist.objects.filter(name__istartswith=letter) \
        .filter(user=user) \
        .filter(album__isnull=False) \
        .annotate(album_count=Count("album"))

    song_counts: QuerySet[Artist] = Artist.objects.filter(name__istartswith=letter) \
        .filter(user=user) \
        .annotate(song_count=Count("song"))

    album_counts_dict: Dict[str, int] = {}
    for artist in album_counts:
        # mypy doesn't understand Django's annotate(), so we use getattr with type ignore
        album_counts_dict[str(artist.uuid)] = getattr(artist, "album_count")  # type: ignore[attr-defined]

    song_counts_dict: Dict[str, int] = {}
    for artist in song_counts:
        # mypy doesn't understand Django's annotate(), so we use getattr with type ignore
        song_counts_dict[str(artist.uuid)] = getattr(artist, "song_count")  # type: ignore[attr-defined]

    return {
        "album_counts": album_counts_dict,
        "song_counts": song_counts_dict
    }
