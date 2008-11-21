import Image
import re

from os.path import exists, getmtime, dirname
from os import makedirs
from nexus.archive.pdfutil import nameof
from django.conf import settings
from django.template import Context
from django.template.loader import get_template

THUMB_MAX_SIZE = (100,100)
ARTICLE_MAX_SIZE = (530,2048) # remember to sync with images.css
SMALL_MAX_SIZE = (255,2048) # remeber to sync with images.css
THUMBS_PATH = 'cache/image_thumbs/'

def autoclass(obj, tags):
    for tag in tags:
        if tag.slug.startswith('cartoon') or tag.slug.startswith('comic'):
            return 'cartoon:'
    if obj.image.width < 200 and obj.image.height < 200:
        return 'thumb:'
    if obj.image.width < 500 or float(obj.image.height) / float(obj.image.width) > .70:
        return 'small:'
    return ''

def resize(input, max_size, hq):
    if hq:
        name = '@%ix%i.png' % max_size
    else:
        name = '@%ix%i.jpg' % max_size
    name = nameof(input) + name
    relpath = THUMBS_PATH + name
    output_file = settings.MEDIA_ROOT + relpath
    output_url = settings.MEDIA_URL + relpath
    if not exists(dirname(output_file)):
        makedirs(dirname(output_file))
    if not exists(output_file) or getmtime(output_file) < getmtime(input):
        image = Image.open(input)
        image = image.convert('RGBA')
        if hq:
            image.thumbnail(max_size, Image.BICUBIC)
            image.save(output_file, 'PNG')
        else:
            image.thumbnail(max_size, Image.ANTIALIAS)
            image.save(output_file, 'JPEG', quality=85)
    return output_url

def get_right_size(obj, classes):
    if 'small' in classes:
        return obj.small_size()
    elif 'thumb' in classes:
        return obj.thumbnail_size()
    else:
        return obj.article_size()

class ImageFormatter():
    IMAGE_TEMPLATE = 'image.html'
    IMAGE_TAG = re.compile(r'\[\[[:\-_a-z0-9]+]]')

    def __init__(self, html, img_objs):
        self.html = html
        self.images = dict([(obj.slug, obj) for obj in img_objs])

    def __process_match(self, match):
        hunk = match.group()[2:-2]
        classes = hunk.split(':')[:-1]
        template_type = None
        obj = self.images.get(hunk.split(':')[-1])
        if obj:
            template = get_template(self.IMAGE_TEMPLATE)
            viewlink = '/image/' + obj.slug
            any_not_staff = False
            for author in obj.authors.all():
                if not author.nexus_staff:
                    any_not_staff = True
            return template.render(Context({
                'any_not_staff': any_not_staff,
                'image': get_right_size(obj, classes),
                'slug': obj.slug, 'authors': obj.authors.all(), 'caption': obj.caption,
                'viewlink': viewlink, 'classes': ' '.join(classes)
            }))
        else:
            return hunk

    def format(self):
        return self.IMAGE_TAG.sub(self.__process_match, self.html)
