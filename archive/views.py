# Create your views here.

from datetime import date
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.conf import settings
from models import Issue
from nexus.cover.models import InfoPage
from nexus.cover.util import *

def visible(x):
    return x.filter(date__lte=date.today())

def issue_gallery(request, temp='gallery.html'):
    """Thumbnail gallery of front pages."""
    MEDIA_URL = settings.MEDIA_URL
    issues = visible(Issue.objects)
    FOOTER = InfoPage.objects.all();
    common_css = MEDIA_URL
    years = []
    for issue in issues:
        year = what_school_year(issue.date)
        if not years or years[-1].year != year:
            years.append(SchoolYear(year))
        years[-1].append(issue)
    return render_json('Issue Archive', temp, locals())

def issue_gallery_b(request):
    return issue_gallery(request, 'gallery-b.html')

def page_gallery(request, issue, title=None):
    """Previews of each page in the selected issue."""
    MEDIA_URL = settings.MEDIA_URL
    issue = get_object_or_404(Issue, date=issue)
    FOOTER = InfoPage.objects.all();
    if not title:
        title = issue.date
    return render_json(title, 'issue.html', locals())

def current_page_gallery(request):
    """Previews of each page in the selected issue."""
    MEDIA_URL = settings.MEDIA_URL
    for x in Issue.objects.all():
        if x.current():
            issue = x;
            break
    if not issue:
        raise Http404
    return page_gallery(request, issue.date, "Current Issue")
