# Create your views here.
import json
import re

from cover.models import Article, Tag, Image
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import get_template
from django.template import Context
from django.views.decorators.http import require_POST
from nexus import settings

image_tag_re = re.compile(r'\[\[|]]')

def frontpage(request):
    jquery = settings.MEDIA_URL + "jquery.js"
    tags = list(Tag.objects.all())
    tags.sort(key=lambda tag: tag.article_set.count(), reverse=True)
    for num, tag in enumerate(tags):
        tag.num = num % 6
    articles = Article.objects.all()[0:10]
    return render_to_response('frontpage.html', locals())

def imageview(request, slug):
    try:
        obj = Image.objects.get(slug=slug) 
    except IndexError:
        raise Http404
    return render_to_response('imageview.html', locals())

def replace_images(images, hunk):
    # TODO: check and see if more flexibility is required
    if hunk.startswith('thumb:'):
        hunk = hunk[6:]
        template = get_template('thumb.html')
    else:
        template = get_template('image.html')
    obj = images.get(hunk)
    if obj:
        viewlink = '/image/' + obj.slug
        return template.render(Context({'obj': obj, 'viewlink': viewlink}))
    else:
        return hunk

def articlepage(request, year, month, slug):
    try:
        article = Article.objects.get(slug=slug)
    except:
        raise Http404
    images = dict([(obj.slug, obj) for obj in article.images.all()])
    template = get_template('article.html')
    html = image_tag_re.split(template.render(Context({'article': article})))
    html = [ replace_images(images, hunk) for hunk in html ]
    return HttpResponse(''.join(html))

def tagpage(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    articles = tag.article_set.all()
    return render_to_response('tag.html', locals())

def contains(test_set, required_tags):
    for tag in required_tags:
        if tag not in test_set:
            return False
    return True

@require_POST
def more_tag(request):
    tag = Tag.objects.get(slug=request.POST['slug'])
    selected_tags = request.POST.getlist('selected')
    have_articles = request.POST.getlist('have')
    articles = tag.article_set.all()[0:10] #! FIXME arbitrary limit
    response = json.write([{'tagclasses': article.tagclasses.split(" "),
                            'slug': article.slug,
                            'html':'<li class="%s"><h3><a href="%s">%s</a></h3>%s</li>' % (article.tagclasses, article.slug, article.title, article.snippet)
                            }
                           for article in articles if article.slug not in have_articles and contains([tag.slug for tag in article.tags.all()], selected_tags)])
    return HttpResponse(response, mimetype="application/json")
