from django.conf.urls.defaults import *
from django.conf import settings
from cover.views import *
from archive.views import *

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
    (r'^ajax/embed/(\d{4})/(\d{2})/([-_a-z0-9]+)/$', articlepage),
    (r'^ajax/embed/author/([-_a-z0-9]+)$', authorpage),
    (r'^ajax/embed/image/([-_a-z0-9]+)/$', imageview),
    (r'^ajax/embed/tag/([-_a-z0-9]+)$', tagpage),
    (r'^ajax/embed/info/staff$', staff_auto_infopage),
    (r'^ajax/embed/info/([-_a-z0-9]+)$', infopage),
    (r'^ajax/paginator$', paginate),

    (r'^archive/$', issue_gallery),
    (r'^archive/(\d{4}-\d{2}-\d{2})/$', page_gallery),

    (r'^(\d{4})/(\d{2})/([-_a-z0-9]+)/$', wrap(articlepage)),
    (r'^image/([-_a-z0-9]+)/$', wrap(imageview)),
    (r'^tag/([-_a-z0-9]+)$', wrap(tagpage)),
    (r'^author/([-_a-z0-9]+)$', wrap(authorpage)),
    (r'^info/staff$', wrap(staff_auto_infopage)),
    (r'^info/([-_a-z0-9]+)$', wrap(infopage)),
)

    # Do not use in production!
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
