from django.conf.urls.defaults import *
from cover.views import frontpage, articlepage, tagpage

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
    (r'^(\d{4,4})/(\d{2,2})/([-a-z]+)$', articlepage),
    (r'^tag/(.+)$', tagpage),
)
