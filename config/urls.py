from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from accounts import views as accounts_views
from accounts.views import UserProfileDetailView
from blob import views as blob_views
from blob.views import (BlobDeleteView, BlobDetailView, BlobThumbnailView,
                        BlobUpdateView, DocumentCreateView)
from book.views import BookListView
from bookmark import views as bookmark_views
from collection import views as collection_views
from collection.views import (CollectionCreateView, CollectionDeleteView, CollectionDetailView,
                              CollectionListView, CollectionUpdateView)
from drill import views as drill_views
from drill.views import (DrillListView, DrillSearchListView,
                         QuestionCreateView, QuestionDeleteView,
                         QuestionDetailView, QuestionUpdateView)
from feed import views as feed_views
from feed.views import FeedListView, FeedSubscriptionListView
from fitness import views as fitness_views
from fitness.views import ExerciseDetailView
from homepage import views as homepage_views
from music import views as music_views
from music.views import (AlbumDetailView, MusicListJson, WishListCreateView,
                         WishListDetailView, WishListView)
from search import views as search_views
from search.views import SearchListView, SearchTagDetailView
from tag import views as tag_views
from todo.views import (TodoCreateView, TodoDeleteView, TodoDetailView,
                        TodoListView)

admin.autodiscover()


urlpatterns = [

    path('admin/', admin.site.urls),

    path('', homepage_views.homepage, name='homepage'),
    path('homepage/get_calendar_events.json', homepage_views.get_calendar_events, name='get_calendar_events'),

    path('blob/add', DocumentCreateView.as_view(), name='blob_add'),
    path('blob/<uuid:uuid>/delete', BlobDeleteView.as_view(), name='blob_delete'),
    path('blob/metadata_name_search/', blob_views.metadata_name_search, name='metadata_name_search'),
    path('blob/get_amazon_metadata/<str:title>', blob_views.get_amazon_metadata, name='get_amazon_metadata'),
    path('blob/get_amazon_image_info/<str:sha1sum>/<int:index>', blob_views.get_amazon_image_info, name='get_amazon_image_info'),
    path('blob/get_amazon_image_info/<str:sha1sum>', blob_views.get_amazon_image_info, name='get_amazon_image_info'),
    path('blob/set_amazon_image_info/<str:sha1sum>/<int:index>', blob_views.set_amazon_image_info, name='set_amazon_image_info'),
    path('blob/create_thumbnail/<uuid:uuid>/<int:page_number>', blob_views.create_thumbnail, name='create_thumbnail'),
    path('blob/mutate', blob_views.collection_mutate, name='collection_mutate'),
    path('blob/parse_date/<path:input_date>', blob_views.parse_date, name='parse_date'),
    path('blob/slideshow', blob_views.slideshow, name='blob_slideshow'),
    path('blob/<uuid:uuid>', BlobDetailView.as_view(), name='blob_detail'),
    path('blob/<uuid:uuid>/edit', BlobUpdateView.as_view(), name='blob_edit'),
    path('blob/<uuid:uuid>/thumbnail', BlobThumbnailView.as_view(), name='blob_thumbnail'),

    path('notes/', SearchListView.as_view(), {'notes_search': True}, name='notes_list'),

    path('bookmarks/add_note', bookmark_views.add_note, name='bookmark_add_note'),
    path('bookmarks/click<int:bookmark_id>', bookmark_views.click, name='bookmark_click'),
    path('bookmarks/edit/<int:bookmark_id>', bookmark_views.edit, name='bookmark_edit'),
    path('bookmarks/edit', bookmark_views.edit, name='bookmark_add'),
    path('bookmarks/import', bookmark_views.do_import, name='bookmark_import'),
    path('bookmarks/random/', bookmark_views.get_random_bookmarks, name='get_random_bookmarks'),
    path('bookmarks/search/<str:search>', bookmark_views.search, name='bookmark_search'),
    path('bookmarks/snarf_link.html', bookmark_views.snarf_link),

    path('bookmarks/list/', bookmark_views.list, name='bookmark_list'),
    path('bookmarks/list/<int:page_number>', bookmark_views.list, name='bookmark_list'),

    path('bookmarks/tag/sort', bookmark_views.sort_favorite_tags, name='sort_favorite_tags'),
    path('bookmarks/tag/<str:tag_filter>', bookmark_views.list, name='bookmark_tag'),
    path('bookmarks/tagsearch/', bookmark_views.tag_search, name='bookmark_tag_search'),
    path('bookmarks/sort_bookmarks.json', bookmark_views.sort_bookmarks, name='sort_bookmarks'),
    path('bookmarks/delete/<int:bookmark_id>', bookmark_views.delete, name='bookmark_delete'),

    path('books/(\w+)?', BookListView.as_view(), name="book_list"),

    path('collection/embedded/<int:collection_id>', CollectionDetailView.as_view(), {'embedded': True}, name='collection_embedded'),
    path('collection/add', CollectionCreateView.as_view(), name='collection_add'),
    path('collection/delete/<int:pk>', CollectionDeleteView.as_view(), name='collection_delete'),
    path('collection/edit/<int:pk>', CollectionUpdateView.as_view(), name='collection_edit'),
    path('collection/<int:collection_id>/', CollectionDetailView.as_view(), name='collection_detail'),
    path('collection/get_info', collection_views.get_info, name='collection_get_info'),
    path('collection/sort', collection_views.sort_collection, name='sort_collection'),
    path('collection/', CollectionListView.as_view(), name='collection_list'),

    path('drill/', DrillListView.as_view(), name='drill_list'),
    path('drill/question/delete/<int:pk>', QuestionDeleteView.as_view(), name='question_delete'),
    path('drill/question/<int:question_id>/', QuestionDetailView.as_view(), name='question_detail'),
    path('drill/question/add/', QuestionCreateView.as_view(), name='question_add'),
    path('drill/question/edit/<int:pk>/', QuestionUpdateView.as_view(), name='question_edit'),
    path('drill/search/', DrillSearchListView.as_view(), name='drill_search'),
    path('drill/answer/<int:question_id>/', drill_views.show_answer, name='answer'),
    path('drill/response/<int:question_id>/<str:response>', drill_views.record_response, name='record_response'),
    path('drill/study/tag/<str:tag>', drill_views.study_tag, name='study_tag'),
    path('drill/tagsearch/', drill_views.tag_search, name='drill_tag_search'),

    path('feed/sort_feed/', feed_views.sort_feed, name='sort_feed'),
    path('feed/edit/<int:feed_id>', feed_views.feed_edit, name='feed_edit'),
    path('feed/edit', feed_views.feed_edit, name='feed_add'),
    path('feed/subscriptions', FeedSubscriptionListView.as_view(), name='feed_subscriptions'),
    path('feed/check_url/<str:url>', feed_views.check_url, name='check_url'),
    path('feed/subscribe', feed_views.feed_subscribe, name='feed_subscribe'),
    path('feed/unsubscribe', feed_views.feed_unsubscribe, name='feed_unsubscribe'),
    path('feeds/', FeedListView.as_view(), name="feed_list"),

    path('fitness/add/<int:exercise_id>', fitness_views.fitness_add, name='fitness_add'),
    path('fitness/change_active_status', fitness_views.change_active_status, name='change_active_status'),
    path('fitness/<int:exercise_id>', ExerciseDetailView.as_view(), name='exercise_detail'),
    path('fitness/', fitness_views.fitness_summary, name='fitness_summary'),

    path('music/edit/<int:song_id>', music_views.song_edit, name='song_edit'),
    path('music/add', music_views.add_song, name='add_song'),
    path('music/album/<int:pk>', AlbumDetailView.as_view(), name='album_detail'),
    path('music/artist/<str:artist_name>', music_views.artist_detail, name='artist_detail'),
    path('music/datatable/data/', MusicListJson.as_view(), name='get_song_list'),
    path('music/album_artwork/<int:song_id>', music_views.album_artwork, name='album_artwork'),
    path('music/search.json', music_views.search, name='music_search'),
    path('music/song/<int:id>', music_views.get_song_info, name='get_song_info'),
    path('music/wishlistadd', WishListCreateView.as_view(), name='wishlist_add'),
    path('music/wishlist/edit/<int:pk>', WishListDetailView.as_view(), name='wishlist_edit'),
    path('music/wishlist/delete/<int:wishlist_id>', music_views.wishlist_delete, name='wishlist_delete'),
    path('music/wishlist', WishListView.as_view(), name='wishlist'),
    path('music/', music_views.music_list, name='music_list'),

    path('prefs/store_in_session/', accounts_views.store_in_session, name='store_in_session'),
    path('prefs/', UserProfileDetailView.as_view(), name='prefs'),
    path('login/', accounts_views.bc_login, name="login"),
    path('logout', accounts_views.bc_logout, name="logout"),

    path('kb/search/admin', search_views.search_admin, name='search_admin'),
    path('kb/search/tagstitle', search_views.kb_search_tags_booktitles, name='kb_search_tags_booktitles'),
    re_path(r'^kb/search/tagdetail/(?P<taglist>.*)', SearchTagDetailView.as_view(), name='kb_search_tag_detail'),
    path('kb/search/tagdetail/', SearchTagDetailView.as_view(), name='kb_search_tag_detail_search'),
    path('kb/search/', SearchListView.as_view(), name='search'),

    path('tag/search', tag_views.tag_search, name='tag_search'),
    path('tag/add_favorite', tag_views.add_favorite_tag, name='add_favorite_tag'),
    path('tag/remove_favorite', tag_views.remove_favorite_tag, name='remove_favorite_tag'),

    path('todo/add', TodoCreateView.as_view(), name='todo_add'),
    path('todo/edit/<int:pk>', TodoDetailView.as_view(), name='todo_edit'),
    path('todo/delete/<int:pk>', TodoDeleteView.as_view(), name='todo_delete'),
    path('todo/', TodoListView.as_view(), name='todo_list'),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

handler404 = 'homepage.views.handler404'
