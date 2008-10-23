# Create your views here.

from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404
from django.conf import settings
from models import Issue
from nexus.cover.models import InfoPage
from nexus.cover.views import visible, what_school_year, SchoolYear

def issue_gallery(request):
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
    return render_to_response("gallery.html", locals())

def page_gallery(request, issue):
    """Previews of each page in the selected issue."""
    MEDIA_URL = settings.MEDIA_URL
    issue = get_object_or_404(Issue, date=issue)
    FOOTER = InfoPage.objects.all();
    return render_to_response("issue.html", locals())

def current_page_gallery(request):
    """Previews of each page in the selected issue."""
    MEDIA_URL = settings.MEDIA_URL
    for x in Issue.objects.all():
        if x.current():
            issue = x;
            break
    if not issue:
        raise Http404
    FOOTER = InfoPage.objects.all();
    return render_to_response("issue.html", locals())
