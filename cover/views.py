# Create your views here.

from cover.models import Article, Tag
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.http import require_POST

import json

def frontpage(request):
    from nexus.settings import MEDIA_URL ## FIXME
    tags = Tag.objects.all()
    for num, tag in enumerate(tags):
        tag.num = num % 6
    articles = Article.objects.all()[0:10]
    return render_to_response('frontpage.html', locals())

def articlepage(request, year, month, slug):
    try:
        article = Article.objects.filter(slug=slug)[0]
    except IndexError:
        raise Http404
    return HttpResponse(article.title)

def tagpage(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    articles = tag.article_set.all()
    return render_to_response('tag.html', locals())

@require_POST
def more_tag(request):
    tag = Tag.objects.get(slug=request.POST['slug'])
    articles = tag.article_set.all()[0:10]
    response = json.write([{'tagclasses': article.tagclasses.split(" "),
                            'html':'<li class="%s"><h3><a href="%s">%s</a></h3>%s</li>' % (article.tagclasses, article.slug, article.title, article.snippet)
                            }
                           for article in articles])
    return HttpResponse(response, mimetype="application/json")
