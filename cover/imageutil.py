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

image_tag_re = re.compile(r'\[\[|]]')
image_templates = {
    'thumb': get_template('thumb.html'),
}
DEFAULT_TEMPLATE = get_template('image.html')
SCAN_LENGTH = 0
for k,v in image_templates.items():
    SCAN_LENGTH = 1 + max(len(k), SCAN_LENGTH)

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
        if max_size[0]*max_size[1] < 50000:
            image.thumbnail(max_size, Image.ANTIALIAS)
        else:
            image.thumbnail(max_size, Image.BICUBIC)
        image.save(output_file)
    return output_url

def __process_hunk(images, hunk):
    template_type = None
    index = hunk.find(':', 0, SCAN_LENGTH)
    if index >= 0:
        template_type = hunk[0:index]
        hunk = hunk[index+1:]
    obj = images.get(hunk)
    if obj:
        template = image_templates.get(template_type, DEFAULT_TEMPLATE)
        viewlink = '/image/' + obj.slug
        return template.render(Context({'obj': obj, 'viewlink': viewlink}))
    else:
        return hunk

def format_images(html, img_objs):
    hunks = image_tag_re.split(html)
    images = dict([(obj.slug, obj) for obj in img_objs])
    return ''.join([ __process_hunk(images, hunk) for hunk in hunks ])
