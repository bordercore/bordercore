from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.views import login, logout
from django.contrib import admin

from tastypie.api import Api

from bookmark.api import BookmarkResource, UserResource
from bookmark.views import OrderListJson

admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(BookmarkResource())

urlpatterns = patterns('',
                        (r'^api/', include(v1_api.urls)),
)

urlpatterns += patterns('homepage.views',
                        url(r'^$|^index.html', 'homepage', name='homepage')
)

urlpatterns += patterns('blog.views',
                        url(r'^blog/(?:(\d+)/)?edit', 'blog_edit'),
                        url(r'^blog/tag_search.json', 'tag_search'),
                        url(r'^blog/(\d+)?', 'blog_list'),
)

urlpatterns += patterns('feed.views',
                        url(r'^feeds/', 'feed_list')
)

urlpatterns += patterns('bookmark.views',
                        url(r'^bookmarks/edit(?:/(\d+))?', 'bookmark_edit', name='bookmark_edit'),
                        url(r'^bookmarks/snarf_link.html', 'snarf_link'),
                        url(r'^bookmarks/', 'bookmark_list'),
                        url(r'^my/datatable/data/$', OrderListJson.as_view(), name='get_bookmarks_list'),
)

# urlpatterns += patterns('bcsolr.views',
#                        url(r'^solr/search$', 'search')
# )


urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    (r'^accounts/login/$',  login, {'template_name': 'login.html'}),
    (r'^accounts/logout/$', logout),
)
