from django.urls import path

from . import views

app_name = "music"

urlpatterns = [
    path(
        route="create/",
        view=views.SongCreateView.as_view(),
        name="create"
    ),
    path(
        route="search_artist",
        view=views.search_artists,
        name="search_artists"
    ),
    path(
        route="update/<uuid:song_uuid>/",
        view=views.SongUpdateView.as_view(),
        name="update"
    ),
    path(
        route="album/<uuid:uuid>/",
        view=views.AlbumDetailView.as_view(),
        name="album_detail"
    ),
    path(
        route="artist/<str:artist>/",
        view=views.ArtistDetailView.as_view(),
        name="artist_detail"
    ),
    path(
        route="recent_songs",
        view=views.RecentSongsListView.as_view(),
        name="recent_songs"
    ),
    path(
        route="song/<uuid:uuid>",
        view=views.get_song_info,
        name="get_song_info"
    ),
    path(
        route="tag/",
        view=views.SearchTagListView.as_view(),
        name="search_tag"
    ),
    path(
        route="",
        view=views.music_list,
        name="list"
    ),
    path(
        route="get_song_id3_info",
        view=views.get_song_id3_info,
        name="get_song_id3_info"
    ),
    path(
        route="delete/<uuid:uuid>/",
        view=views.MusicDeleteView.as_view(),
        name="delete"
    ),
]
