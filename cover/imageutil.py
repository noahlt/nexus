import Image
import re

from os.path import basename, exists, getmtime, dirname
from os import makedirs
from django.template import Context
from django.template.loader import get_template
from nexus import settings

THUMB_MAX_SIZE = (150,250)
ARTICLE_MAX_SIZE = (800,600)
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
    DEFAULT_TEMPLATE = get_template('image.html')
    IMAGE_TAG = re.compile(r'\[\[[:\-_a-z0-9]+]]')
    TEMPLATES = {
        'thumb': get_template('thumb.html'),
    }

    def __init__(self, html, img_objs):
        self.html = html
        self.images = dict([(obj.slug, obj) for obj in img_objs])

    def __process_match(self, match):
        hunk = match.group()[2:-2]
        template_type = None
        index = hunk.find(':')
        if index >= 0:
            template_type = hunk[0:index]
            hunk = hunk[index+1:]
        obj = self.images.get(hunk)
        if obj:
            template = self.TEMPLATES.get(template_type, self.DEFAULT_TEMPLATE)
            viewlink = '/image/' + obj.slug
            return template.render(Context({'obj': obj, 'viewlink': viewlink}))
        else:
            return hunk

    def format(self):
        return self.IMAGE_TAG.sub(self.__process_match, self.html)
