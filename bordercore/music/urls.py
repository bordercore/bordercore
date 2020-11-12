from django.urls import path

from . import views

app_name = "collection"

urlpatterns = [
    path(
        route="update/<int:song_id>/",
        view=views.song_update,
        name="song_update"
    ),
    path(
        route="create/",
        view=views.create_song,
        name="create_song"
    ),
    path(
        route="album/<int:pk>/",
        view=views.AlbumDetailView.as_view(),
        name="album_detail"
    ),
    path(
        route="artist/<str:artist_name>/",
        view=views.artist_detail,
        name="artist_detail"
    ),
    path(
        route="datatable/data/",
        view=views.MusicListJson.as_view(),
        name="get_song_list"
    ),
    path(
        route="album_artwork/<int:song_id>",
        view=views.album_artwork,
        name="album_artwork"
    ),
    path(
        route="search/",
        view=views.search,
        name="search"
    ),
    path(
        route="song/<int:id>",
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
]
