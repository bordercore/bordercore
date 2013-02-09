from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.views import login, logout
from django.contrib import admin

from bookmark.views import OrderListJson

admin.autodiscover()

urlpatterns = patterns('homepage.views',
                        url(r'^$|^index.html', 'homepage', name='homepage')
)

urlpatterns += patterns('blog.views',
                        url(r'^blog/(?:(\d+)/)?edit', 'blog_edit'),
                        url(r'^blog/(\d+)?', 'blog_list'),
                        url(r'^blog/tag_search.json', 'tag_search')
)

urlpatterns += patterns('feed.views',
                        url(r'^feeds/', 'feed_list')
)

urlpatterns += patterns('bookmark.views',
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
