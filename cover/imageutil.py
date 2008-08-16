import Image

from os.path import basename, exists, getmtime, dirname
from os import makedirs
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
        image.thumbnail(max_size)
        image.save(output_file)
    return output_url
