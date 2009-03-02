from nexus.archive.models import Issue
from nexus.archive.views import *
from django.conf import settings
from django.shortcuts import get_object_or_404, render_to_response
from django.template import Context
from django.views.decorators.cache import never_cache
from models import Article, StaticPage, InfoPage, Author, Tag, Image
import simplejson as json
import views

def test(function):
    @never_cache
    def minimal_wrap(*args):
        response = json.loads(function(*args).content)
        return render_to_response('minimal.html', Context({'MEDIA_URL': settings.MEDIA_URL, 'content': response['html'], 'title': response['title']}))
    return minimal_wrap

def _preview_article(request, object_id):
    article = get_object_or_404(Article, id=object_id)
    return test(views._articlepage)(request, article)

def _preview_tag(request, object_id):
    tag = get_object_or_404(Tag, id=object_id)
    return test(views.tagpage)(request, tag.slug)

def _preview_image(request, object_id):
    image = get_object_or_404(Image, id=object_id)
    return test(views.imageview)(request, image.slug)

def _preview_staticpage(request, object_id):
    page = get_object_or_404(StaticPage, id=object_id)
    return test(views.staticpage)(request, page.slug)

def _preview_infopage(request, object_id):
    page = get_object_or_404(InfoPage, id=object_id)
    if page.slug == 'staff':
        return test(views.staff_auto_infopage)(request)
    else:
        return test(views.infopage)(request, page.slug)

def _preview_issue(request, object_id):
    issue = get_object_or_404(Issue, id=object_id)
    return test(page_gallery)(request, issue.date)
