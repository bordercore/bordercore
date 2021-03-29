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
        route="pin/",
        view=views.pin,
        name="pin"
    ),
    path(
        route="unpin/",
        view=views.unpin,
        name="unpin"
    ),
]
