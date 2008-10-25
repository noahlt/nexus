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

    # Uncomment the next line for to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    (r'^$', frontpage),
    (r'^null/', lambda x: HttpResponse('')),
    (r'^ajax/embed/(\d{4})/(\d{2})/([-_a-z0-9]+)/$', articlepage),
    (r'^ajax/embed/author/([-_a-z0-9]+)$', authorpage),
    (r'^ajax/embed/image/([-_a-z0-9]+)/$', imageview),
    (r'^ajax/embed/tag/([-_a-z0-9]+)$', tagpage),
    (r'^ajax/embed/info/staff$', staff_auto_infopage),
    (r'^ajax/embed/info/([-_a-z0-9]+)$', infopage),
    (r'^ajax/embed/static/([-_a-z0-9]+)$', staticpage),
    (r'^ajax/embed/archive/$', issue_gallery),
    (r'^ajax/embed/archive/current/$', current_page_gallery),
    (r'^ajax/embed/archive/(\d{4}-\d{2}-\d{2})/$', page_gallery),
    (r'^ajax/paginator$', paginate),

    (r'^(\d{4})/(\d{2})/([-_a-z0-9]+)/$', wrap(articlepage)),
    (r'^image/([-_a-z0-9]+)/$', wrap(imageview)),
    (r'^tag/([-_a-z0-9]+)$', wrap(tagpage)),
    (r'^author/([-_a-z0-9]+)$', wrap(authorpage)),
    (r'^info/staff$', wrap(staff_auto_infopage)),
    (r'^info/([-_a-z0-9]+)$', wrap(infopage)),
    (r'^static/([-_a-z0-9]+)$', wrap(staticpage)),
    (r'^archive/$', wrap(issue_gallery)),
    (r'^archive/current/$', wrap(current_page_gallery)),
    (r'^archive/(\d{4}-\d{2}-\d{2})/$', wrap(page_gallery)),

    (r'^test/(\d{4})/(\d{2})/([-_a-z0-9]+).*$', test(articlepage)),
    (r'^test/image/([-_a-z0-9]+).*$', test(imageview)),
    (r'^test/tag/([-_a-z0-9]+).*$', test(tagpage)),
    (r'^test/author/([-_a-z0-9]+).*$', test(authorpage)),
    (r'^test/info/staff.*$', test(staff_auto_infopage)),
    (r'^test/info/([-_a-z0-9]+).*$', test(infopage)),
    (r'^test/static/([-_a-z0-9]+).*$', test(staticpage)),
    (r'^test/archive/(\d{4}-\d{2}-\d{2}).*$', test(page_gallery)),
    (r'^test/archive/current.*$', test(current_page_gallery)),
    (r'^test/archive.*$', test(issue_gallery)),
)
if settings.DEBUG: # not in production!
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
