# Create your views here.
import re
import simplejson as json

from cover.models import *
from datetime import date, timedelta
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, Template
from django.template.loader import get_template
from imageutil import ImageFormatter
from models import Issue

PAGE_SIZE = 10

def __visible(x):
    return x.filter(date__lte=date.today())

def what_school_year(date):
    if date.month <= 7:
        return date.year
    return date.year + 1

def staticpage(request, slug):
    obj = get_object_or_404(StaticPage, slug=slug)
    return HttpResponse(obj.html)

def frontpage(request, content=None):
    MEDIA_URL = settings.MEDIA_URL
    FOOTER = InfoPage.objects.all()
    sidelinks = SideBarLink.objects.all()
    tags = [ tag for tag in Tag.objects.all() if __visible(tag.article_set).count() > 0 ]
    tags.sort(key=lambda tag: __visible(tag.article_set).count(), reverse=True)
    if not content:
        paginator = Paginator(__visible(Article.objects), PAGE_SIZE)
        articles = paginator.page(1).object_list
    try:
        current_issue = __visible(Issue.objects)[0]
    except IndexError:
        current_issue = False
    # `dates` looks like this:
    #   [[2009, date, date, date], [2008, date, date, date]]
    class Schoolyear(list):
        def __init__(self, year, dates):
            self.year = year
            self.dates = dates
    dates = []
    for date in __visible(Article.objects).dates('date', 'month', order='DESC'):
        year = what_school_year(date)
        if not dates or dates[-1].year != year:
            dates.append(Schoolyear(year, [date]))
        else:
            dates[-1].dates.append(date)
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
            titles.append((title, authors_for_title))
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

def __tag_data(articles, selected_tags):
    alltags = {}
    for article in articles:
        for tag in article.tags.all():
            if tag in alltags:
                alltags[tag] += 1
            else:
                alltags[tag] = 1
    total = articles.count()
    return [ (tag.slug, tag in selected_tags or alltags[tag] != total) for tag in alltags.keys() ]

def __dates_of(articles):
    return list(set([article.date.strftime('%Y%m') for article in articles.all()]))

def __parse_date(input):
    '''Turns an integer date like 200801 into a datetime object like
    datetime.date(2008, 1, 1)'''
    strdate = str(input)
    year = int(strdate[0:4])
    month = int(strdate[4:6])
    return date(year, month, 1)

def __month_end(d):
    '''Takes a datetime.date and returns the date for the last day in the
    same month.'''
    return date(d.year if d.month < 12 else d.year + 1, d.month+1 if d.month < 12 else 1, d.day) - timedelta(1)

def wrap(function):
    def wrapped(*args):
        return frontpage(args[0], function(*args).content)
    return wrapped

def paginate(request):
    tags = Tag.objects.filter(slug__in=request.GET.getlist('tags'))
    have_articles = request.GET.getlist('have_articles')
    min_date = __parse_date(request.GET.get('date_min'))
    max_date = __month_end(__parse_date(request.GET.get('date_max')))
    articles = __visible(Article.objects)
    for tag in tags:
        articles = articles.filter(tags=tag)
    dates = __dates_of(articles) # BEFORE date filtering
    articles = articles.filter(date__range=[min_date, max_date])
    paginator = Paginator(articles, PAGE_SIZE)
    object_list = paginator.page(request.GET.get('page', 1)).object_list
    results = [get_template('article_snippet.html') \
               .render(Context({'article': article}))
               for article in object_list if article.slug not in have_articles ]
    r = {'results': {'new': results, 'all': [ article.slug for article in object_list ]},
         'tags': __tag_data(articles, tags), 'dates': dates,
         'pages': {'num_pages': paginator.num_pages, 'this_page': request.GET.get('page', 1)}}
    return HttpResponse(json.dumps(r), mimetype="application/json")
