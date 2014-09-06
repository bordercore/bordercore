from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import logout
from tastypie.api import Api

from accounts.api import UserResource
from accounts.views import UserProfileDetailView
from bookmark.api import BookmarkResource
from bookmark.views import OrderListJson
from book.views import BookListView
from feed.views import FeedListView, FeedSubscriptionListView
from music.api import MusicWishListResource
from music.views import MusicListJson, WishListView, WishListCreateView, WishListDetailView
from todo.api import TodoResource
from todo.views import TodoCreateView, TodoDeleteView, TodoDetailView, TodoListView
from search.views import SearchListView, SearchTagDetailView

admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(BookmarkResource())
v1_api.register(TodoResource())
v1_api.register(MusicWishListResource())

urlpatterns = patterns('',
                        (r'^api/', include(v1_api.urls)),
)

urlpatterns += patterns('homepage.views',
                        url(r'^$|^index.html', 'homepage', name='homepage'),
                        url(r'^homepage/get_calendar_events.json', 'get_calendar_events', name='get_calendar_events'),
)

urlpatterns += patterns('blog.views',
                        url(r'^blog/edit(?:/(\d+))?', 'blog_edit', name='blog_edit'),
                        url(r'^blog/(\d+)?', 'blog_list', name='blog_list'),
)

urlpatterns += patterns('book.views',
                        url(r'^books/(\w+)?', BookListView.as_view(), name="book_list")
)

urlpatterns += patterns('document.views',
                        url(r'^kb/documents(?:/(\d+))?/edit', 'document_edit', name='document_edit'),
                        url(r'^kb/documents/(\d+)', 'document_detail', name='document_detail'),
)

urlpatterns += patterns('feed.views',
                        url(r'^feed/sort_feed/', 'sort_feed', name='sort_feed'),
                        url(r'^feed/edit(?:/(\d+))?', 'feed_edit', name='feed_edit'),
                        url(r'^feed/subscriptions', FeedSubscriptionListView.as_view(), name='feed_subscriptions'),
                        url(r'^feed/check_url/(.*)', 'check_url', name='check_url'),
                        url(r'^feed/subscribe', 'feed_subscribe', name='feed_subscribe'),
                        url(r'^feed/unsubscribe', 'feed_unsubscribe', name='feed_unsubscribe'),
                        url(r'^feeds/', FeedListView.as_view(), name="feed_list"),
)

urlpatterns += patterns('bookmark.views',
                        url(r'^bookmarks/edit(?:/(\d+))?', 'bookmark_edit', name='bookmark_edit'),
                        url(r'^bookmarks/snarf_link.html', 'snarf_link'),
                        url(r'^bookmarks/tag/', 'bookmark_tag', name='bookmark_tag'),
                        url(r'^bookmarks/tagsearch/', 'tag_search', name='tag_search'),
                        url(r'^bookmarks/tag_bookmark_list.json', 'tag_bookmark_list', name='tag_bookmark_list'),
                        url(r'^bookmarks/delete/(\d+)', 'bookmark_delete', name='bookmark_delete'),
                        url(r'^bookmarks/', 'bookmark_list', name='bookmark_list'),
                        url(r'^my/datatable/data/$', OrderListJson.as_view(), name='get_bookmarks_list'),
)

urlpatterns += patterns('music.views',
                        url(r'^music/edit(?:/(\d+))?', 'song_edit', name='song_edit'),
                        url(r'^music/add', 'add_song', name='add_song'),
                        url(r'^music/album/(\d+)', 'show_album', name='show_album'),
                        url(r'^music/artist/(.*)', 'show_artist', name='show_artist'),
                        url(r'^music/datatable/data/$', MusicListJson.as_view(), name='get_song_list'),
                        url(r'^music/stream/(\d+)?', 'music_stream', name='music_stream'),
                        url(r'^music/album_artwork/(\w+)?', 'album_artwork', name='album_artwork'),
                        url(r'^music/search.json', 'search', name='music_search'),
                        url(r'^music/wishlistadd', WishListCreateView.as_view(), name='wishlist_add'),
                        url(r'^music/wishlist/edit/(?P<pk>[\d-]+)$', WishListDetailView.as_view(), name='wishlist_edit'),
                        url(r'^music/wishlist', WishListView.as_view(), name='wishlist'),
                        url(r'^music/', 'music_list', name='music_list'),
)

urlpatterns += patterns('todo.views',
                        url(r'^todo/add', TodoCreateView.as_view(), name='todo_add'),
                        url(r'^todo/edit/(?P<pk>[\d-]+)$', TodoDetailView.as_view(), name='todo_edit'),
                        url(r'^todo/delete/(?P<pk>[\d-]+)$', TodoDeleteView.as_view(), name='todo_delete'),
                        url(r'^todo/', TodoListView.as_view(), name='todo_list'),
)

urlpatterns += patterns('search.views',
                        url(r'^kb/search/admin', 'search_admin', name='search_admin'),
                        url(r'^kb/search/booktitle', 'search_book_title', name='search_book_title'),
                        url(r'^kb/search/tagstitle', 'kb_search_tags_booktitles', name='kb_search_tags_booktitles'),
                        url(r'^kb/search/tagdetail/(?P<tag>.*)', SearchTagDetailView.as_view(), name='kb_search_tag_detail'),
                        url(r'^kb/search/', SearchListView.as_view(), name='search')
)

urlpatterns += patterns('tag.views',
                        url(r'^tag/search', 'tag_search', name='tag_search')
)

urlpatterns += patterns('accounts.views',
                        url(r'^prefs/store_in_session/', 'store_in_session', name='store_in_session'),
                        url(r'^prefs/', UserProfileDetailView.as_view(), name='prefs'),
)

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('accounts.views',
    url(r'^login/', 'bc_login'),
    url(r'^logout', logout, {'template_name': 'login.html'}),
)

handler404 = 'site_utils.handler404'
