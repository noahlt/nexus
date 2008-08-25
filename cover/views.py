# Create your views here.
import simplejson as json

from cover.models import Article, Tag, Image, Author, InfoPage, Title
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context
from django.template.loader import get_template
from imageutil import ImageFormatter
from models import Issue
from nexus import settings

def frontpage(request):
    MEDIA_URL = settings.MEDIA_URL
    FOOTER = InfoPage.objects.all();
    num_to_load = 5
    tags = [ tag for tag in Tag.objects.all() if tag.article_set.count() > 0 ]
    tags.sort(key=lambda tag: tag.article_set.count(), reverse=True)
    total = Article.objects.count()
    remaining = total - num_to_load
    articles = Article.objects.all()[0:num_to_load]
    try:
        current_issue = Issue.objects.get(date=date.today())
        newtags = set()
        for article in current_issue.article_set.all():
            for tag in article.tags.all():
                newtags.add(tag)
        for tag in tags:
            tag.new = tag in newtags
        tags.sort(key=lambda tag: tag.new and 1 or 0, reverse=True)
        showprint = True
    except ObjectDoesNotExist:
        current_issue = Issue.objects.all().reverse()[0]
        showprint = False
    return render_to_response('frontpage.html', locals())

def imageview(request, slug):
    MEDIA_URL = settings.MEDIA_URL
    FOOTER = InfoPage.objects.all();
    obj = get_object_or_404(Image, slug=slug)
    return render_to_response('imageview.html', locals())

def staff_auto_infopage(request):
    MEDIA_URL = settings.MEDIA_URL
    FOOTER = InfoPage.objects.all();
    info = get_object_or_404(InfoPage, slug='staff')
    pool = Author.objects.filter(retired=False).filter(nexus_staff=True).all()
    titles = []
    groups = []
    for title in Title.objects.all():
        authors_for_title = [ [author, []] for author in pool.filter(title=title) ]
        if authors_for_title:
            titles.append((title, authors_for_title))
            for author in authors_for_title:
                for group in author[0].subauthors.all():
                    if group.nexus_staff:
                        if group not in groups:
                            groups.append(group)
                        author[1].append(groups.index(group) + 1)
    return render_to_response('staff.html', locals())

def infopage(request, slug):
    MEDIA_URL = settings.MEDIA_URL
    FOOTER = InfoPage.objects.all();
    info = get_object_or_404(InfoPage, slug=slug)
    return render_to_response('info.html', locals())

def articlepage(request, year, month, slug):
    article = get_object_or_404(Article, slug=slug)
    html = get_template('article.html').render(Context(
        {'article': article, 'MEDIA_URL': settings.MEDIA_URL,
         'FOOTER': InfoPage.objects.all()}
    ))
    html = ImageFormatter(html, article.images.all()).format()
    return HttpResponse(html)

def tagpage(request, slug):
    FOOTER = InfoPage.objects.all();
    MEDIA_URL = settings.MEDIA_URL
    tag = get_object_or_404(Tag, slug=slug)
    return render_to_response('tag.html', locals())

def authorpage(request, slug):
    FOOTER = InfoPage.objects.all();
    MEDIA_URL = settings.MEDIA_URL
    author = get_object_or_404(Author, slug=slug)
    authors = [ x for x in author.subauthors.all() if x.nexus_staff ]
    return render_to_response('author.html', locals())

def tag_data_for(articles, selected_tags):
    # FIXME very inefficient lookup
    alltags = {}
    for article in articles.all():
        for tag in article.tags.all():
            if tag in alltags:
                alltags[tag] += 1
            else:
                alltags[tag] = 1
    total = articles.count()
    return [ (tag.slug, tag in selected_tags or alltags[tag] != total) for tag in alltags.keys() ]


def stat_articles(request):
    data = request.GET
    tags = Tag.objects.filter(slug__in=data.getlist('tagslugs'))
    articles = Article.objects.all();
    for tag in tags:
        articles = articles.filter(tags=tag)
    total = articles.count()
    extra_tag_data = tag_data_for(articles, tags)
    articles = articles.exclude(slug__in=data.getlist('have_articles'))
    stats = {
        'stats': {'total': total, 'remaining': max(0, articles.count())},
        'tags': extra_tag_data
    }
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
    extra_tag_data = tag_data_for(articles, tags)
    articles = articles.exclude(slug__in=data.getlist('have_articles'))
    stats = {'total': total, 'remaining': max(0, articles.count() - num_to_load)}
    article_data = [{'tagclasses': article.tagclasses.split(' '),
          'slug': article.slug,
          'html': get_template('article_snippet.html') \
                      .render(Context({'article': article,
                                       'hidden': True}))
    } for article in articles[0:num_to_load]]
    r = {'stats': stats, 'articles': article_data, 'tags': extra_tag_data}
    return HttpResponse(json.write(r), mimetype="application/json")
