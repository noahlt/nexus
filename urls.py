from django.conf.urls.defaults import *
from django.conf import settings
from django.http import HttpResponse
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

    (r'^admin/[^/]+/(?P<type>[^/]+)/(?P<object_id>[0-9]+)/preview/$', preview),
    (r'^admin/(.*)', admin.site.root),

    (r'^$', some_frontpage),
    (r'^null/', lambda x: HttpResponse('')),
    (r'^ajax/embed/cover/$', frontpage_static_contents),
    (r'^ajax/embed/(\d{4})/(\d{2})/([-_a-zA-Z0-9]+)/$', articlepage),
    (r'^ajax/embed/author/([-_a-zA-Z0-9]+)$', authorpage),
    (r'^ajax/embed/image/([-_a-zA-Z0-9]+)/$', imageview),
    (r'^ajax/embed/tag/([-_a-zA-Z0-9]+)$', tagpage),
    (r'^ajax/embed/info/staff$', staff_auto_infopage),
    (r'^ajax/embed/info/([-_a-zA-Z0-9]+)$', infopage),
    (r'^ajax/embed/static/([-_a-zA-Z0-9]+)$', staticpage),
    (r'^ajax/embed/poll_history$', pollhist),
    (r'^ajax/embed/archive/$', issue_gallery),
    (r'^ajax/embed/archive-b/$', issue_gallery_b),
    (r'^ajax/embed/archive/current/$', current_page_gallery),
    (r'^ajax/embed/archive/(\d{4}-\d{2}-\d{2})/$', page_gallery),
    (r'^ajax/paginator$', paginate),
    (r'^ajax/poll/$', poll_results),
    (r'^ajax/poll/current$', poll_view),

    (r'^(\d{4})/(\d{2})/([-_a-zA-Z0-9]+)/$', wrap(articlepage)),
    (r'^image/([-_a-zA-Z0-9]+)/$', wrap(imageview)),
    (r'^tag/([-_a-zA-Z0-9]+)$', wrap(tagpage)),
    (r'^author/([-_a-zA-Z0-9]+)$', wrap(authorpage)),
    (r'^info/staff$', wrap(staff_auto_infopage)),
    (r'^info/([-_a-zA-Z0-9]+)$', wrap(infopage)),
    (r'^static/([-_a-zA-Z0-9]+)$', wrap(staticpage)),
    (r'^poll_history$', wrap(pollhist)),
    (r'^archive/$', wrap(issue_gallery)),
    (r'^archive-b/$', wrap(issue_gallery_b)),
    (r'^archive/current/$', wrap(current_page_gallery)),
    (r'^archive/(\d{4}-\d{2}-\d{2})/$', wrap(page_gallery)),
    (r'^(\d+)$', frontpage_paginated),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
