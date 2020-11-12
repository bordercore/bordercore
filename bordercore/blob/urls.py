from django.urls import path

from . import views

app_name = "blob"

urlpatterns = [
    path(
        route="<uuid:uuid>/",
        view=views.BlobDetailView.as_view(),
        name="detail"
    ),
    path(
        route="<uuid:uuid>/update/",
        view=views.BlobUpdateView.as_view(),
        name="update"
    ),
    path(
        route="<uuid:uuid>/thumbnail/",
        view=views.BlobThumbnailView.as_view(),
        name="thumbnail"
    ),
    path(
        route="create/",
        view=views.BlobCreateView.as_view(),
        name="create"
    ),
    path(
        route="<uuid:uuid>/delete/",
        view=views.BlobDeleteView.as_view(),
        name="delete"
    ),
    path(
        route="metadata_name_search/",
        view=views.metadata_name_search,
        name="metadata_name_search"
    ),
    path(
        route="create_thumbnail/<uuid:uuid>/<int:page_number>/",
        view=views.create_thumbnail,
        name="create_thumbnail"
    ),
    path(
        route="mutate/",
        view=views.collection_mutate,
        name="collection_mutate"
    ),
    path(
        route="parse_date/<path:input_date>/",
        view=views.parse_date,
        name="parse_date"
    ),
    path(
        route="slideshow/",
        view=views.slideshow,
        name="slideshow"
    ),
]
