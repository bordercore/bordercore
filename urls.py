from django.conf.urls import patterns, include, url
from django.contrib.auth.views import logout
from django.contrib import admin

from tastypie.api import Api

from bookmark.api import BookmarkResource, UserResource, TodoResource
from bookmark.views import OrderListJson
from music.views import MusicListJson
from accounts.views import UserProfileDetailView
from todo.views import TodoCreateView, TodoDeleteView, TodoDetailView, TodoListView

admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(BookmarkResource())
v1_api.register(TodoResource())

urlpatterns = patterns('',
                        (r'^api/', include(v1_api.urls)),
)

urlpatterns += patterns('homepage.views',
                        url(r'^$|^index.html', 'homepage', name='homepage')
)

urlpatterns += patterns('blog.views',
                        url(r'^blog/edit(?:/(\d+))?', 'blog_edit', name='blog_edit'),
                        url(r'^blog/tag_search.json', 'tag_search', name='blog_tag_search'),
                        url(r'^blog/(\d+)?', 'blog_list', name='blog_list'),
)

urlpatterns += patterns('feed.views',
                        url(r'^feed/sort_feed/', 'sort_feed', name='sort_feed'),
                        url(r'^feeds/', 'feed_list', name="feed_list"),
)

urlpatterns += patterns('bookmark.views',
                        url(r'^bookmarks/edit(?:/(\d+))?', 'bookmark_edit', name='bookmark_edit'),
                        url(r'^bookmarks/snarf_link.html', 'snarf_link'),
                        url(r'^bookmarks/tag_search.json', 'tag_search', name='bookmark_tag_search'),
                        url(r'^bookmarks/tag/', 'bookmark_tag', name='bookmark_tag'),
                        url(r'^bookmarks/tag_bookmark_list.json', 'tag_bookmark_list', name='tag_bookmark_list'),
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
                        url(r'^music/album_artwork/(\d+)?', 'album_artwork', name='album_artwork'),
                        url(r'^music/search.json', 'search', name='music_search'),
                        url(r'^music/', 'music_list', name='music_list'),
)

urlpatterns += patterns('todo.views',
                        url(r'^todo/add', TodoCreateView.as_view(), name='todo_add'),
                        url(r'^todo/edit/(?P<pk>[\d-]+)$', TodoDetailView.as_view(), name='todo_edit'),
                        url(r'^todo/delete/(?P<pk>[\d-]+)$', TodoDeleteView.as_view(), name='todo_delete'),
                        url(r'^todo/', TodoListView.as_view(), name='todo_list'),
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
