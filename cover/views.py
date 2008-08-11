# Create your views here.

from cover.models import Article, Tag
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404



def frontpage(request):
    from nexus.settings import MEDIA_URL ## FIXME

    tags = Tag.objects.all()
    for num, tag in enumerate(tags):
        tag.num = num % 6
        
    articles = Article.objects.all()[0:10]
    # Article tags are stored (in slug form) as the classes of the li's that
    # wrap articles, so the js doesn't have to look up article tags itself.
    for article in articles:
        article.tagclasses = ' '.join(tag.slug for tag in article.tags.all())

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
