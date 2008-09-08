# Create your views here.
import simplejson as json

from cover.models import Article, Tag, Image, Author, InfoPage, Title
from datetime import date
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, Template
from django.template.loader import get_template
from imageutil import ImageFormatter
from models import Issue
from nexus import settings

PAGE_SIZE = 10

def __visible(x):
    return x.filter(date__lte=date.today())

def frontpage(request):
    MEDIA_URL = settings.MEDIA_URL
    FOOTER = InfoPage.objects.all();
    tags = [ tag for tag in Tag.objects.all() if __visible(tag.article_set).count() > 0 ]
    tags.sort(key=lambda tag: __visible(tag.article_set).count(), reverse=True)
    paginator = Paginator(__visible(Article.objects), PAGE_SIZE)
    articles = paginator.page(1).object_list
    current_issue = __visible(Issue.objects)[0]
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
    pool = Author.objects.filter(retired=False, nexus_staff=True).all()
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
    if not article.current() \
        or article.date.year != int(year) \
        or article.date.month != int(month):
            raise Http404
    template = Template(article.custom_template.template) \
        if article.custom_template else get_template('article.html')
    html = template.render(Context(
        {'article': article, 'MEDIA_URL': settings.MEDIA_URL,
         'FOOTER': InfoPage.objects.all()}
    ))
    html = ImageFormatter(html, article.images.all()).format()
    return HttpResponse(html)

def futurepage(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if article.current():
        raise Http404
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

def __tag_data(articles, selected_tags):
    alltags = {}
    articles = __visible(articles)
    for article in articles:
        for tag in article.tags.all():
            if tag in alltags:
                alltags[tag] += 1
            else:
                alltags[tag] = 1
    total = articles.count()
    return [ (tag.slug, tag in selected_tags or alltags[tag] != total) for tag in alltags.keys() ]

def paginate(request):
    tags = Tag.objects.filter(slug__in=request.GET.getlist('tags'))
    have_articles = request.GET.getlist('have_articles')
    articles = __visible(Article.objects)
    for tag in tags:
        articles = articles.filter(tags=tag)
    paginator = Paginator(articles, PAGE_SIZE)
    object_list = paginator.page(request.GET.get('page', 1)).object_list
    results = [get_template('article_snippet.html') \
               .render(Context({'article': article}))
               for article in object_list if article.slug not in have_articles ]
    r = {'results': {'new': results, 'all': [ article.slug for article in object_list ]},
         'tags': __tag_data(articles, tags),
         'pages': {'num_pages': paginator.num_pages, 'this_page': request.GET.get('page', 1)}}
    return HttpResponse(json.dumps(r), mimetype="application/json")
