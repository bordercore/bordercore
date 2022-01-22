from django.urls import path

from . import views

app_name = "node"

urlpatterns = [
    path(
        route="",
        view=views.NodeListView.as_view(),
        name="list"
    ),
    path(
        route="<uuid:uuid>/",
        view=views.NodeDetailView.as_view(),
        name="detail"
    ),
    path(
        route="<uuid:uuid>/blob_list/",
        view=views.get_blob_list,
        name="get_blob_list"
    ),
    path(
        route="<uuid:uuid>/note/",
        view=views.get_note,
        name="get_note"
    ),
    path(
        route="blob/edit_note/",
        view=views.edit_blob_note,
        name="edit_blob_note"
    ),
    path(
        route="blob/remove/",
        view=views.remove_blob,
        name="remove_blob"
    ),
    path(
        route="blob/sort/",
        view=views.sort_blobs,
        name="sort_blobs"
    ),
    path(
        route="bookmark/add/",
        view=views.add_bookmark,
        name="add_bookmark"
    ),
    path(
        route="blob/add/",
        view=views.add_blob,
        name="add_blob"
    ),
    path(
        route="edit_note/",
        view=views.edit_note,
        name="edit_note"
    )
]
