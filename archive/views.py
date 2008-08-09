# Create your views here.

from django.shortcuts import render_to_response, get_object_or_404
from archive.models import Issue

def issue_gallery(request):
    issues = Issue.objects.all()
    return render_to_response("gallery.html", locals())

def page_gallery(request, issue):
    issue = get_object_or_404(Issue, date=issue)
    return render_to_response("issue.html", locals())
