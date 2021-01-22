from rest_framework import routers

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from api.views import (AlbumViewSet, BlobViewSet, BookmarkViewSet,
                       CollectionViewSet, FeedViewSet, QuestionViewSet,
                       SongSourceViewSet, SongViewSet, TagViewSet, TodoViewSet,
                       UserViewSet)
from book.views import BookListView
from homepage.views import handler403, handler404, handler500

admin.autodiscover()

urlpatterns = [

    path("admin/", admin.site.urls),
    path(r"books/(\w+)?", BookListView.as_view(), name="book_list"),

]

for app in ("accounts", "blob", "bookmark", "collection", "drill", "feed", "fitness", "metrics", "music", "node", "search", "tag", "todo"):
    urlpatterns += [
        path(f"{app}/", include(f"{app}.urls", namespace=app)),
    ]

urlpatterns += [
    path("", include("homepage.urls", namespace="homepage")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]

router = routers.DefaultRouter()
router.register(r"albums", AlbumViewSet, "Album")
router.register(r"blobs", BlobViewSet, "Blob")
router.register(r"bookmarks", BookmarkViewSet, "Bookmark")
router.register(r"collections", CollectionViewSet, "Collection")
router.register(r"feeds", FeedViewSet, "Feed")
router.register(r"questions", QuestionViewSet, "Question")
router.register(r"songs", SongViewSet, "Song")
router.register(r"songsources", SongSourceViewSet, "SongSource")
router.register(r"tags", TagViewSet, "Tag")
router.register(r"todos", TodoViewSet, "Todo")
router.register(r"users", UserViewSet, "User")

urlpatterns += [
    url(r"^api/", include(router.urls)),
    path("", include("rest_framework.urls", namespace="rest_framework"))
]

handler403 = "homepage.views.handler403"
handler404 = "homepage.views.handler404"
handler500 = "homepage.views.handler500"
