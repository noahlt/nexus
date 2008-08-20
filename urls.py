from django.conf.urls.defaults import *
from cover.views import frontpage, articlepage, \
    tagpage, load_more_articles, imageview, authorpage, stat_articles
from archive.views import issue_gallery, page_gallery
from nexus import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^nexus/', include('nexus.foo.urls')),

    # Uncomment the next line to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line for to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    (r'^$', frontpage),
    (r'^(\d{4})/(\d{2})/([-_a-z0-9]+)/$', articlepage),
    (r'^archive/$', issue_gallery),
    (r'^archive/(\d{4}-\d{2}-\d{2})/$', page_gallery),
    (r'^ajax/more_articles$', load_more_articles),
    (r'^ajax/stat_articles$', stat_articles),
    (r'^image/([-_a-z0-9]+)/$', imageview),
    (r'^tag/([-_a-z0-9]+)$', tagpage),
    (r'^people/([-_a-z0-9]+)$', authorpage),
)

    # Do not use in production!
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
