# Create your views here.
import simplejson as json

from cover.models import Article, Tag, Image, Author
from django.http import HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context
from django.template.loader import get_template
from nexus import settings
from imageutil import ImageFormatter

def frontpage(request):
    MEDIA_URL = settings.MEDIA_URL
    num_to_load = 5
    tags = list(Tag.objects.all())
    tags.sort(key=lambda tag: tag.article_set.count(), reverse=True)
    for num, tag in enumerate(tags):
        tag.num = num % 6
    total = Article.objects.count()
    remaining = total - num_to_load
    articles = Article.objects.all()[0:num_to_load]
    return render_to_response('frontpage.html', locals())

def imageview(request, slug):
    MEDIA_URL = settings.MEDIA_URL
    try:
        obj = Image.objects.get(slug=slug) 
    except ObjectDoesNotExist:
        raise Http404
    return render_to_response('imageview.html', locals())

def articlepage(request, year, month, slug):
    try:
        article = Article.objects.get(slug=slug)
    except ObjectDoesNotExist:
        raise Http404
    html = get_template('article.html').render(Context(
        {'article': article, 'MEDIA_URL': settings.MEDIA_URL}
    ))
    html = ImageFormatter(html, article.images.all()).format()
    return HttpResponse(html)

def tagpage(request, slug):
    MEDIA_URL = settings.MEDIA_URL
    tag = get_object_or_404(Tag, slug=slug)
    return render_to_response('tag.html', locals())

def authorpage(request, slug):
    MEDIA_URL = settings.MEDIA_URL
    author = get_object_or_404(Author, slug=slug)
    return render_to_response('author.html', locals())

def stat_articles(request):
    data = request.GET
    tags = Tag.objects.filter(slug__in=data.getlist('tagslugs'))
    articles = Article.objects.all();
    for tag in tags:
        articles = articles.filter(tags=tag)
    total = articles.count()
    articles = articles.exclude(slug__in=data.getlist('have_articles'))
    stats = {'total': total, 'remaining': max(0, articles.count())}
    return HttpResponse(json.write(stats), mimetype="application/json")

def load_more_articles(request):
    num_to_load = 5
    data = request.GET
    tags = Tag.objects.filter(slug__in=data.getlist('tagslugs'))
    articles = Article.objects.all();

    # by repeatedly applying a new filter for each tag, we get an AND filter,
    # while articles.filter(tags__in=tags) would give us an OR filter.
    for tag in tags:
        articles = articles.filter(tags=tag)
    total = articles.count()
    articles = articles.exclude(slug__in=data.getlist('have_articles'))
    stats = {'total': total, 'remaining': max(0, articles.count() - num_to_load)}
    article_data = [{'tagclasses': article.tagclasses.split(' '),
          'slug': article.slug,
          'html': get_template('article_snippet.html') \
                      .render(Context({'article': article,
                                       'hidden': True}))
    } for article in articles[0:num_to_load]]

    r = {'stats': stats, 'articles': article_data}
    return HttpResponse(json.write(r), mimetype="application/json")
