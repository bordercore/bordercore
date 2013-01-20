from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.views import login, logout
#from bcsolr.views import search

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('blog.views',
                        url(r'^blog/(?:(\d+)/)?edit', 'blog_edit'),
                        url(r'^blog/(\d+)?', 'blog_list'),
                        url(r'^blog/tag_search.json', 'tag_search')
)

urlpatterns += patterns('feed.views',
                        url(r'^feeds/', 'feed_list')
)

# urlpatterns += patterns('bcsolr.views',
#                        url(r'^solr/search$', 'search')
# )


urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    (r'^accounts/login/$',  login, {'template_name': 'bcsolr/login.html'}),
    (r'^accounts/logout/$', logout),
)
