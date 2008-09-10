# Create your views here.

from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from datetime import date
from archive.models import Issue
from nexus.cover.models import InfoPage

def __visible(x):
    return x.filter(date__lte=date.today())

class Year(list):
    def __init__(self, year, issues):
        self.year = year
        self.extend(issues)

    def __str__(self):
        return super.__str__(self)

def issue_gallery(request):
    """Thumbnail gallery of front pages."""
    MEDIA_URL = settings.MEDIA_URL
    issues = __visible(Issue.objects)
    FOOTER = InfoPage.objects.all();
    common_css = MEDIA_URL
    years = [Year(date.year, issues.filter(date__year=date.year))
            for date in issues.dates('date', 'year')]
    return render_to_response("gallery.html", locals())

def page_gallery(request, issue):
    """Previews of each page in the selected issue."""
    MEDIA_URL = settings.MEDIA_URL
    issue = get_object_or_404(Issue, date=issue)
    FOOTER = InfoPage.objects.all();
    return render_to_response("issue.html", locals())
