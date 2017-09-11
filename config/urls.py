from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import logout

from accounts import views as accounts_views
from accounts.api import UserResource
from accounts.views import UserProfileDetailView
from blob import views as blob_views
from blob.views import (BlobDeleteView, BlobDetailView, BlobUpdateView,
                        BlogListView, DocumentCreateView)
from book.views import BookListView
from bookmark import views as bookmark_views
from bookmark.api import BookmarkResource
from bookmark.views import OrderListJson
from collection import views as collection_views
from collection.views import (CollectionCreateView, CollectionDetailView,
                              CollectionListView, CollectionUpdateView)
from feed import views as feed_views
from feed.views import FeedListView, FeedSubscriptionListView
from fitness import views as fitness_views
from fitness.views import ExerciseDetailView
from homepage import views as homepage_views
from music import views as music_views
from music.api import MusicWishListResource
from music.views import (AlbumDetailView, MusicListJson, WishListCreateView,
                         WishListDetailView, WishListView)
from search import views as search_views
from search.views import SearchListView, SearchTagDetailView
from tag import views as tag_views
from tastypie.api import Api
from todo.api import TodoResource
from todo.views import (TodoCreateView, TodoDeleteView, TodoDetailView,
                        TodoListView)

admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(BookmarkResource())
v1_api.register(TodoResource())
v1_api.register(MusicWishListResource())

urlpatterns = [

    url(r'^api/', include(v1_api.urls)),

    url(r'^admin/', admin.site.urls),

    url(r'^$|^index.html', homepage_views.homepage, name='homepage'),
    url(r'^homepage/get_calendar_events.json', homepage_views.get_calendar_events, name='get_calendar_events'),

    url(r'^blob/add', DocumentCreateView.as_view(), name='blob_add'),
    # url(r'^blob/upload', blob_views.blob_upload, name='blob_upload'),
    url(r'^blob/(?P<uuid>[0-9a-f-]+)/delete$', BlobDeleteView.as_view(), name='blob_delete'),
    url(r'^blob/metadata_name_search/', blob_views.metadata_name_search, name='metadata_name_search'),
    # url(r'^blob/get_amazon_metadata/(?P<title>[\w|\W]+)$', blob_views.get_amazon_metadata, name='get_amazon_metadata'),
    # url(r'^blob/get_amazon_image_info/(?P<sha1sum>[\w|\W]+)/(?P<index>\d+)$', blob_views.get_amazon_image_info, name='get_amazon_image_info'),
    # url(r'^blob/get_amazon_image_info/(?P<sha1sum>[\w|\W]+)$', blob_views.get_amazon_image_info, name='get_amazon_image_info'),
    # url(r'^blob/set_amazon_image_info/(?P<sha1sum>[\w|\W]+)/(?P<index>\d+)$', blob_views.set_amazon_image_info, name='set_amazon_image_info'),
    url(r'^blob/mutate', blob_views.collection_mutate, name='collection_mutate'),
    url(r'^blob/(?P<uuid>[0-9a-f-]+)$', BlobDetailView.as_view(), name='blob_detail'),
    url(r'^blob/(?P<uuid>[0-9a-f-]+)/edit$', BlobUpdateView.as_view(), name='blob_edit'),

    url(r'^blog/(\d+)?', BlogListView.as_view(), name='blog_list'),

    url(r'^bookmarks/click(?:/(\d+))?', bookmark_views.bookmark_click, name='bookmark_click'),
    url(r'^bookmarks/edit(?:/(\d+))?', bookmark_views.bookmark_edit, name='bookmark_edit'),
    url(r'^bookmarks/snarf_link.html', bookmark_views.snarf_link),
    url(r'^bookmarks/tag/', bookmark_views.bookmark_tag, name='bookmark_tag'),
    url(r'^bookmarks/tagsearch/', bookmark_views.tag_search, name='tag_search'),
    url(r'^bookmarks/tag_bookmark_list.json', bookmark_views.tag_bookmark_list, name='tag_bookmark_list'),
    url(r'^bookmarks/delete/(\d+)', bookmark_views.bookmark_delete, name='bookmark_delete'),
    url(r'^bookmarks/', bookmark_views.bookmark_list, name='bookmark_list'),
    url(r'^my/datatable/data/$', OrderListJson.as_view(), name='get_bookmarks_list'),

    url(r'^books/(\w+)?', BookListView.as_view(), name="book_list"),

    url(r'^collection/embedded/(?P<collection_id>\d+)$', CollectionDetailView.as_view(), {'embedded': True}, name='collection_embedded'),
    url(r'^collection/add', CollectionCreateView.as_view(), name='collection_add'),
    url(r'^collection/edit/(?P<pk>[\d-]+)$', CollectionUpdateView.as_view(), name='collection_edit'),
    url(r'^collection/(?P<collection_id>\d+)$', CollectionDetailView.as_view(), name='collection_detail'),
    url(r'^collection/get_info', collection_views.get_info, name='collection_get_info'),
    url(r'^collection/sort', collection_views.sort_collection, name='sort_collection'),
    url(r'^collection/', CollectionListView.as_view(), name='collection_list'),

    url(r'^feed/sort_feed/', feed_views.sort_feed, name='sort_feed'),
    url(r'^feed/edit(?:/(\d+))?', feed_views.feed_edit, name='feed_edit'),
    url(r'^feed/subscriptions', FeedSubscriptionListView.as_view(), name='feed_subscriptions'),
    url(r'^feed/check_url/(.*)', feed_views.check_url, name='check_url'),
    url(r'^feed/subscribe', feed_views.feed_subscribe, name='feed_subscribe'),
    url(r'^feed/unsubscribe', feed_views.feed_unsubscribe, name='feed_unsubscribe'),
    url(r'^feeds/', FeedListView.as_view(), name="feed_list"),

    url(r'^fitness/add/(?P<exercise_id>\d+)$', fitness_views.fitness_add, name='fitness_add'),
    url(r'^fitness/change_active_status', fitness_views.change_active_status, name='change_active_status'),
    url(r'^fitness/(?P<exercise_id>\d+)$', ExerciseDetailView.as_view(), name='exercise_detail'),
    url(r'^fitness/', fitness_views.fitness_summary, name='fitness_summary'),

    url(r'^music/edit(?:/(\d+))?', music_views.song_edit, name='song_edit'),
    url(r'^music/add', music_views.add_song, name='add_song'),
    url(r'^music/album/(?P<pk>.*)$', AlbumDetailView.as_view(), name='album_detail'),
    url(r'^music/artist/(.*)', music_views.artist_detail, name='artist_detail'),
    url(r'^music/datatable/data/$', MusicListJson.as_view(), name='get_song_list'),
    url(r'^music/album_artwork/(\w+)?', music_views.album_artwork, name='album_artwork'),
    url(r'^music/search.json', music_views.search, name='music_search'),
    url(r'^music/song/(\d+)$', music_views.get_song_info, name='get_song_info'),
    url(r'^music/wishlistadd', WishListCreateView.as_view(), name='wishlist_add'),
    url(r'^music/wishlist/edit/(?P<pk>[\d-]+)$', WishListDetailView.as_view(), name='wishlist_edit'),
    url(r'^music/wishlist', WishListView.as_view(), name='wishlist'),
    url(r'^music/', music_views.music_list, name='music_list'),

    url(r'^prefs/store_in_session/', accounts_views.store_in_session, name='store_in_session'),
    url(r'^prefs/', UserProfileDetailView.as_view(), name='prefs'),
    url(r'^login/', accounts_views.bc_login, name="login"),
    url(r'^logout', accounts_views.bc_logout, name="logout"),

    url(r'^kb/search/admin', search_views.search_admin, name='search_admin'),
    url(r'^kb/search/booktitle', search_views.search_book_title, name='search_book_title'),
    url(r'^kb/search/tagstitle', search_views.kb_search_tags_booktitles, name='kb_search_tags_booktitles'),
    url(r'^kb/search/tagdetail/(?P<taglist>.*)', SearchTagDetailView.as_view(), name='kb_search_tag_detail'),
    url(r'^kb/search/', SearchListView.as_view(), name='search'),

    url(r'^tag/search', tag_views.tag_search, name='tag_search'),

    url(r'^todo/add', TodoCreateView.as_view(), name='todo_add'),
    url(r'^todo/edit/(?P<pk>[\d-]+)$', TodoDetailView.as_view(), name='todo_edit'),
    url(r'^todo/delete/(?P<pk>[\d-]+)$', TodoDeleteView.as_view(), name='todo_delete'),
    url(r'^todo/', TodoListView.as_view(), name='todo_list'),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

handler404 = 'site_utils.handler404'
