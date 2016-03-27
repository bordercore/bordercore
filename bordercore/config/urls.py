from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import logout
from tastypie.api import Api

from accounts.api import UserResource
from accounts.views import UserProfileDetailView
from blob.views import BlobDeleteView, BlobDetailView, BlobUpdateView
from bookmark.api import BookmarkResource
from bookmark.views import OrderListJson
from bookshelf.views import BookshelfListView
from book.views import BookListView
from feed.views import FeedListView, FeedSubscriptionListView
from fitness.views import ExerciseDetailView
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

urlpatterns += patterns('blob.views',
                        url(r'^blob/add/(\w+)$', 'blob_add', name='blob_add'),
                        url(r'^blob/add', 'blob_add', name='blob_add'),
                        url(r'^blob/delete/(?P<pk>\w+)$', BlobDeleteView.as_view(), name='blob_delete'),
                        url(r'^blob/edit/(?P<sha1sum>\w+)$', BlobUpdateView.as_view(), name='blob_edit'),
                        url(r'^blob/metadata_name_search/', 'metadata_name_search', name='metadata_name_search'),
                        url(r'^blob/get_amazon_metadata/(?P<title>[\w|\W]+)$', 'get_amazon_metadata', name='get_amazon_metadata'),
                        url(r'^blob/get_amazon_image_info/(?P<sha1sum>[\w|\W]+)/(?P<index>\d+)$', 'get_amazon_image_info', name='get_amazon_image_info'),
                        url(r'^blob/get_amazon_image_info/(?P<sha1sum>[\w|\W]+)$', 'get_amazon_image_info', name='get_amazon_image_info'),
                        url(r'^blob/set_amazon_image_info/(?P<sha1sum>[\w|\W]+)/(?P<index>\d+)$', 'set_amazon_image_info', name='set_amazon_image_info'),
                        url(r'^blob/todo', 'blob_todo', name='blob_todo'),
                        url(r'^blob/(?P<sha1sum>\w+)$', BlobDetailView.as_view(), name='blob_detail')
)

urlpatterns += patterns('blog.views',
                        url(r'^blog/edit(?:/(\d+))?', 'blog_edit', name='blog_edit'),
                        url(r'^blog/(\d+)?', 'blog_list', name='blog_list'),
)

urlpatterns += patterns('book.views',
                        url(r'^books/(\w+)?', BookListView.as_view(), name="book_list")
)

urlpatterns += patterns('bookshelf.views',
                        url(r'^bookshelf/add', 'add_to_bookshelf', name='add_to_bookshelf'),
                        url(r'^bookshelf/sort', 'sort_bookshelf', name='sort_bookshelf'),
                        url(r'^bookshelf/remove', 'remove_from_bookshelf', name='remove_from_bookshelf'),
                        url(r'^bookshelf/', BookshelfListView.as_view(), name='bookshelf_list'),
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

urlpatterns += patterns('fitness.views',
                        url(r'^fitness/add/(?P<exercise_id>\d+)$', 'fitness_add', name='fitness_add'),
                        url(r'^fitness/change_active_status', 'change_active_status', name='change_active_status'),
                        url(r'^fitness/(?P<exercise_id>\d+)$', ExerciseDetailView.as_view(), name='exercise_detail'),
                        url(r'^fitness/', 'fitness_summary', name='fitness_summary')
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
                        url(r'^music/album_artwork/(\w+)?', 'album_artwork', name='album_artwork'),
                        url(r'^music/search.json', 'search', name='music_search'),
                        url(r'^music/song/(\d+)$', 'get_song_info', name='get_song_info'),
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
                        url(r'^kb/search/documentsource', 'search_document_source', name='search_document_source'),
                        url(r'^kb/search/tagstitle', 'kb_search_tags_booktitles', name='kb_search_tags_booktitles'),
                        url(r'^kb/search/tagdetail/(?P<taglist>.*)', SearchTagDetailView.as_view(), name='kb_search_tag_detail'),
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
