# Create your views here.
import re
import simplejson as json

from datetime import date, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, Template
from django.template.loader import get_template
from django.views.decorators.cache import never_cache
from imageutil import ImageFormatter
from models import *

PAGE_SIZE = 10
METADATA_CACHE_SECONDS = 3600 * 12

class SchoolYear(list):
    def __init__(self, year):
        self.year = year;
    def __str__(self):
        return '%s-%s' % (self.year-1, self.year)

def visible(x):
    return x.filter(date__lte=date.today())

def pagesof(page, pages, adjacent_pages=3):
    ret = [n for n in range(page - adjacent_pages, page + adjacent_pages + 1) if n > 0 and n <= pages]
    while len(ret) < adjacent_pages*2+1 and ret[-1] < pages:
        ret.append(ret[-1]+1)
    while len(ret) < adjacent_pages*2+1 and ret[0] > 1:
        ret.insert(0,ret[0]-1)
    jump_forward = False
    jump_back = False
    if ret[0] > 1:
        jump_back = True
        ret[0] = 1
    if ret[-1] < pages:
        jump_forward = True
        ret[-1] = pages
    return (ret,jump_forward,jump_back)

def what_school_year(date):
    if date.month <= 7:
        return date.year
    return date.year + 1

def staticpage(request, slug):
    return HttpResponse(get_object_or_404(StaticPage, slug=slug).html)

def frontpage(request, content=None):
    MEDIA_URL = settings.MEDIA_URL
    FOOTER = InfoPage.objects.all()
    sidelinks = SideBarLink.objects.all()
    tags = [ tag for tag in Tag.objects.all()[0:20] if visible(tag.article_set).count() > 0 ]
    tags.sort(key=lambda tag: visible(tag.article_set).count(), reverse=True)
    if not content:
        paginator = Paginator(visible(Article.objects), PAGE_SIZE)
        articles = paginator.page(1).object_list
        pages = paginator.num_pages
        if pages > 1:
            page = 1
            is_paginated = True
            page_numbers, jump_forward, jump_back = pagesof(page, pages)
            previous = None
            next = 2
            has_next = True
            has_previous = False
    try:
        current_issue = visible(Issue.objects)[0]
    except IndexError:
        current_issue = False
    key = 'frontpage_dates_key'
    try:
        key += '%s' % visible(Article.objects)[0]
    except IndexError:
        pass
    dates = cache.get(key)
    if not dates:
        dates = []
        for date in visible(Article.objects).dates('date', 'month', order='DESC'):
            year = what_school_year(date)
            if not dates or dates[-1].year != year:
                dates.append(SchoolYear(year))
            dates[-1].append(date)
        cache.set(key, dates, METADATA_CACHE_SECONDS)
    return HttpResponse(get_template('frontpage.html').render(Context(locals())))

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
            titles.append((title.plural_form if len(authors_for_title) > 1 and title.plural_form else title, authors_for_title))
            for author in authors_for_title:
                for group in author[0].grouping.all():
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
    if article.date.year != int(year) or article.date.month != int(month):
        raise Http404
    template = Template(article.custom_template.template) \
        if article.custom_template else get_template('article.html')
    html = template.render(Context(
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
    authors = [ x for x in author.grouping.all() ]
    return render_to_response('author.html', locals())

def tag_data(articles, selected_tags, min_date, max_date):
    key = 'tag_data' + str((selected_tags, min_date, max_date))
    cached = cache.get(key)
    if cached:
        return cached
    alltags = {}
    for article in articles:
        for tag in article.tags.all():
            if tag in alltags:
                alltags[tag] += 1
            else:
                alltags[tag] = 1
    total = articles.count()
    ret = [(tag.slug, tag in selected_tags or alltags[tag] != total) for tag in alltags.keys()]
    cache.set(key, ret, METADATA_CACHE_SECONDS)
    return ret

def dates_of(articles, tags):
    key = 'date_of' + str(tags)
    cached = cache.get(key)
    if cached:
        return cached
    ret = list(set([article.date.strftime('%Y%m') for article in articles.all()]))
    cache.set(key, ret, METADATA_CACHE_SECONDS)
    return ret

def parse_date(input):
    '''Turns an integer date like 200801 into a datetime object like
    datetime.date(2008, 1, 1)'''
    strdate = str(input)
    year = int(strdate[0:4])
    month = int(strdate[4:6])
    return date(year, month, 1)

def month_end(d):
    '''Takes a datetime.date and returns the date for the last day in the
    same month.'''
    return date(d.year if d.month < 12 else d.year + 1, d.month+1 if d.month < 12 else 1, d.day) - timedelta(1)

def wrap(function):
    def wrapped(*args):
        return frontpage(args[0], function(*args).content)
    return wrapped

def test(function):
    @never_cache
    def minimal_wrap(*args):
        return render_to_response('minimal.html', Context({'MEDIA_URL':settings.MEDIA_URL,'content':function(*args).content}))
    return minimal_wrap

def snippet(article):
    key = 'snippet' + str(article)
    cached = cache.get(key)
    if cached:
        return cached
    ret = get_template('article_snippet.html').render(Context({'article': article}))
    cache.set(key, ret)
    return ret

def paginate(request):
    tags = Tag.objects.filter(slug__in=request.GET.getlist('tags'))
    hash = request.GET.get('hash', '#')
    if hash != '#':
        hash += ','
    have_articles = request.GET.getlist('have_articles')
    min_date = parse_date(request.GET.get('date_min'))
    max_date = month_end(parse_date(request.GET.get('date_max')))
    articles = visible(Article.objects)
    for tag in tags:
        articles = articles.filter(tags=tag)
    dates = dates_of(articles, tags) # BEFORE date filtering
    articles = articles.filter(date__range=[min_date, max_date])
    paginator = Paginator(articles, PAGE_SIZE)
    pages = paginator.num_pages
    page = int(request.GET.get('page',1))
    try:
        object_list = paginator.page(page).object_list
    except (EmptyPage, InvalidPage):
        page = paginator.num_pages
        object_list = paginator.page(page).object_list
    if pages > 1:
        is_paginated = True
        page_numbers, jump_forward, jump_back = pagesof(page, pages)
        next = page + 1
        previous = page - 1
        has_next = (page < pages)
        has_jump = (pages > page_numbers[-1])
        has_previous = (page > 1)
    results = [snippet(article) for article in object_list if article.slug not in have_articles]
    r = {'results': {'new': results, 'all': [ article.slug for article in object_list ]},
         'tags': tag_data(articles, tags, min_date, max_date), 'dates': dates,
         'pages': get_template('paginator.html').render(Context(locals()))}
    return HttpResponse(json.dumps(r), mimetype="application/json")
