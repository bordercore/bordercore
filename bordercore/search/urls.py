from django.urls import path, re_path

from . import views

app_name = "search"

urlpatterns = [
    path(
        route="tagstitle/",
        view=views.kb_search_tags_booktitles,
        name="kb_search_tags_booktitles"
    ),
    re_path(
        route=r"^tagdetail/(?P<taglist>.*)/",
        view=views.SearchTagDetailView.as_view(),
        name="kb_search_tag_detail"
    ),
    path(
        route="tagdetail/",
        view=views.SearchTagDetailView.as_view(),
        name="kb_search_tag_detail_search"
    ),
    path(
        route="",
        view=views.SearchListView.as_view(),
        name="search"
    ),
    path(
        route="notes",
        view=views.NoteListView.as_view(),
        name="notes"
    ),
]
