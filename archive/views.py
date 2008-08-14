# Create your views here.

from django.shortcuts import render_to_response, get_object_or_404
from archive.models import Issue

class Year(list):
    def __init__(self, year, issues):
        self.year = year
        self.extend(issues)

    def __str__(self):
        return super.__str__(self)

def issue_gallery(request):
    """Thumbnail gallery of front pages."""
    issues = Issue.objects.all()
    years = [Year(date.year, issues.filter(date__year=date.year))
            for date in issues.dates('date', 'year')]
    return render_to_response("gallery.html", locals())

def page_gallery(request, issue):
    """Previews of each page in the selected issue."""
    issue = get_object_or_404(Issue, date=issue)
    return render_to_response("issue.html", locals())
