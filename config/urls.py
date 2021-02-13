from rest_framework import routers

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from api.views import (AlbumViewSet, BlobViewSet, BookmarkViewSet,
                       CollectionViewSet, FeedItemViewSet, FeedViewSet,
                       QuestionViewSet, SongSourceViewSet, SongViewSet,
                       TagViewSet, TodoViewSet, UserViewSet)
from book.views import BookListView
from feed.views import update_feed_list
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
router.register(r"albums", AlbumViewSet, "album")
router.register(r"blobs", BlobViewSet, "blob")
router.register(r"bookmarks", BookmarkViewSet, "bookmark")
router.register(r"collections", CollectionViewSet, "collection")
router.register(r"feeds", FeedViewSet, "feed")
router.register(r"feeditem", FeedItemViewSet)
router.register(r"questions", QuestionViewSet, "question")
router.register(r"songs", SongViewSet, "song")
router.register(r"songsources", SongSourceViewSet, "songsource")
router.register(r"tags", TagViewSet, "tag")
router.register(r"todos", TodoViewSet, "todo")
router.register(r"users", UserViewSet, "user")

urlpatterns += [
    url(r"^api/", include(router.urls)),
    path("api/feeds/update_feed_list/<uuid:feed_uuid>/", update_feed_list),
    path("", include("rest_framework.urls", namespace="rest_framework"))
]

# Include any API calls that call outside the usual DRF "CRUD" operations
urlpatterns += [
    path("api/feeds/update_feed_list/<uuid:feed_uuid>/", update_feed_list),
]

handler403 = "homepage.views.handler403"
handler404 = "homepage.views.handler404"
handler500 = "homepage.views.handler500"
