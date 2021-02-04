from django.urls import path

from . import views

app_name = "collection"

urlpatterns = [
    path(
        route="",
        view=views.CollectionListView.as_view(),
        name="list"
    ),
    path(
        route="create/",
        view=views.CollectionCreateView.as_view(),
        name="create"
    ),
    path(
        route="delete/<uuid:collection_uuid>/",
        view=views.CollectionDeleteView.as_view(),
        name="delete"
    ),
    path(
        route="update/<uuid:collection_uuid>/",
        view=views.CollectionUpdateView.as_view(),
        name="update"
    ),
    path(
        route="<uuid:collection_uuid>/",
        view=views.CollectionDetailView.as_view(),
        name="detail"
    ),
    path(
        route="get_info/",
        view=views.get_info,
        name="get_info"
    ),
    path(
        route="get_blob/<int:collection_id>/<int:blob_position>/",
        view=views.get_blob,
        name="get_blob"
    ),
    path(
        route="sort/",
        view=views.sort_collection,
        name="sort"
    ),
]
