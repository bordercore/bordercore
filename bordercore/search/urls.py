from django.urls import path, re_path

from . import views

app_name = "search"

urlpatterns = [
    path(
        route="search/tagstitle/",
        view=views.kb_search_tags_booktitles,
        name="kb_search_tags_booktitles"
    ),
    re_path(
        route=r"^kb/search/tagdetail/(?P<taglist>.*)/",
        view=views.SearchTagDetailView.as_view(),
        name="kb_search_tag_detail"
    ),
    path(
        route="search/tagdetail/",
        view=views.SearchTagDetailView.as_view(),
        name="kb_search_tag_detail_search"
    ),
    path(
        route="search/",
        view=views.SearchListView.as_view(),
        name="search"
    ),
    path(
        route="search/notes",
        view=views.SearchListView.as_view(),
        kwargs={"notes_search": True},
        name="notes"
    ),
]
