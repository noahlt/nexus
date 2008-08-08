# Create your views here.

from django.shortcuts import render_to_response, get_object_or_404
from archive.models import Issue
from pdfutil import pdf_to_thumbnail

def issue_gallery(request):
    issues = Issue.objects.all()
    for issue in issues:
        issue.thumbnail = pdf_to_thumbnail(issue.pages.all()[0].pdf, 256)
    return render_to_response("gallery.html", locals())

def page_gallery(request, issue):
    issue = get_object_or_404(Issue, date=issue)
    for page in issue.pages.all():
        page.thumbnail = pdf_to_thumbnail(page.pdf, 512)
        page.save()
    return render_to_response("issue.html", locals())
