from django.urls import path

from . import views

app_name = "tag"

urlpatterns = [
    path(
        route="search/",
        view=views.tag_search,
        name="search"
    ),
    path(
        route="add_favorite/",
        view=views.add_favorite_tag,
        name="add_favorite_tag"
    ),
    path(
        route="remove_favorite/",
        view=views.remove_favorite_tag,
        name="remove_favorite_tag"
    ),
]
