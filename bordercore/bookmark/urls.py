from django.urls import path

from . import views

app_name = "bookmark"

urlpatterns = [
    path(
        route="add_note/",
        view=views.add_note,
        name="add_note"
    ),
    path(
        route="click/<int:bookmark_id>/",
        view=views.click,
        name="click"
    ),
    path(
        route="edit/<int:bookmark_id>/",
        view=views.edit,
        name="edit"
    ),
    path(
        route="edit/",
        view=views.edit,
        name="add"
    ),
    path(
        route="get_new_bookmarks_count/<int:timestamp>/",
        view=views.get_new_bookmarks_count,
        name="get_new_bookmarks_count"
    ),
    path(
        route="import/",
        view=views.do_import,
        name="import"
    ),
    path(
        route="snarf_link.html",
        view=views.snarf_link,
    ),
    path(
        route="overview/",
        view=views.overview,
        name="overview"
    ),
    path(
        route="list/page/<int:page_number>/",
        view=views.BookmarkListView.as_view(),
        name="get_bookmarks_by_page"
    ),
    path(
        route="list/keyword/<str:search>/",
        view=views.BookmarkListView.as_view(),
        name="get_bookmarks_by_keyword"
    ),
    path(
        route="list/random/",
        view=views.BookmarkListView.as_view(),
        kwargs={"random": True},
        name="get_bookmarks_by_random"
    ),
    path(
        route="list/tag/<str:tag_filter>/",
        view=views.BookmarkListTagView.as_view(),
        name="get_bookmarks_by_tag"
    ),
    path(
        route="tag/sort/",
        view=views.sort_favorite_tags,
        name="sort_favorite_tags"
    ),
    path(
        route="tag/search/",
        view=views.get_tags_used_by_bookmarks,
        name="get_tags_used_by_bookmarks"
    ),
    path(
        route="sort/",
        view=views.sort_bookmarks,
        name="sort"
    ),
    path(
        route="delete/<int:bookmark_id>",
        view=views.delete,
        name="delete"
    ),
]
