import Image
import re

from os.path import basename, exists, getmtime, dirname
from os import makedirs
from django.conf import settings
from django.template import Context
from django.template.loader import get_template

THUMB_MAX_SIZE = (150,150)
ARTICLE_MAX_SIZE = (788,2048)
THUMBS_PATH = 'cache/image_thumbs/'

def resize(input, max_size):
    name = '@%ix%i.png' % max_size
    name = basename(input)[0:-4] + name
    relpath = THUMBS_PATH + name
    output_file = settings.MEDIA_ROOT + relpath
    output_url = settings.MEDIA_URL + relpath
    if not exists(dirname(output_file)):
        makedirs(dirname(output_file))
    if not exists(output_file) or getmtime(output_file) < getmtime(input):
        image = Image.open(input)
        image.thumbnail(max_size, Image.ANTIALIAS)
        image.save(output_file)
    return output_url

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
                'image': obj.thumbnail_size() if 'thumb' in classes else obj.article_size(),
                'slug': obj.slug, 'authors': obj.authors.all(), 'caption': obj.caption,
                'viewlink': viewlink, 'classes': ' '.join(classes)
            }))
        else:
            return hunk

    def format(self):
        return self.IMAGE_TAG.sub(self.__process_match, self.html)
