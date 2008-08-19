# Create your views here.

import json

from cover.models import Article, Tag
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.http import require_POST
from nexus import settings

def frontpage(request):
    MEDIA_URL = settings.MEDIA_URL
    tags = list(Tag.objects.all())
    tags.sort(key=lambda tag: tag.article_set.count(), reverse=True)
    for num, tag in enumerate(tags):
        tag.num = num % 6
    articles = Article.objects.all()[0:2]
    return render_to_response('frontpage.html', locals())

def articlepage(request, year, month, slug):
    try:
        article = Article.objects.get(slug=slug)
    except IndexError:
        raise Http404
    return render_to_response('article.html', locals());

def tagpage(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    articles = tag.article_set.all()
    return render_to_response('tag.html', locals())

def contains(test_set, required_tags):
    for tag in required_tags:
        if tag not in test_set:
            return False
    return True

def load_more_articles(request):
    data = request.GET
    
    tags = Tag.objects.filter(slug__in=data.getlist('tagslugs'))

    articles = Article.objects.exclude(slug__in=data.getlist('have_articles'))

    # by repeatedly applying a new filter for each tag, we get an AND filter,
    # while articles.filter(tags__in=tags) would give us an OR filter.
    for tag in tags:
        articles = articles.filter(tags=tag)

    r = [{'tagclasses': article.tagclasses.split(" "), #FIXME
          'slug': article.slug,
          'html':'<li class="%s new-article"><h3><a href="%s">%s</a></h3>%s</li>' % \
              (article.tagclasses, article.slug, article.title, article.snippet)
          }
         for article in articles[0:2]]

    return HttpResponse(json.write(r), mimetype="application/json")
