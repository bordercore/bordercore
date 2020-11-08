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
        route="embedded/<int:collection_id>/",
        view=views.CollectionDetailView.as_view(),
        kwargs={'embedded': True},
        name="embedded"
    ),
    path(
        route="add/",
        view=views.CollectionCreateView.as_view(),
        name="add"
    ),
    path(
        route="delete/<int:pk>/",
        view=views.CollectionDeleteView.as_view(),
        name="delete"
    ),
    path(
        route="edit/<int:pk>/",
        view=views.CollectionUpdateView.as_view(),
        name="edit"
    ),
    path(
        route="<int:collection_id>/",
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
