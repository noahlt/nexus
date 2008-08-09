#!/usr/bin/env python
import PythonMagick
import Image
from nexus import settings
from os.path import basename, dirname, exists
from django.core.validators import ValidationError
import os

JOIN_PATH = 'cache/joins/'
THUMBS_PATH = 'cache/thumbs/'
STOCK_FAILED_PAGE = settings.MEDIA_ROOT + 'stock/FAILED_PAGE.pdf'

def pdf_validator(field_data, all_data):
    try:
        magic_ok = field_data['content'].startswith('%PDF')
        ext_ok = field_data['filename'].endswith('.pdf')
    except Exception:
        if not field_data.endswith('.pdf'):
            raise ValidationError("That is not a PDF file.")
        return
    if magic_ok and not ext_ok:
        raise ValidationError("Please rename that file so it has a .pdf extension")
    if not magic_ok and ext_ok:
        raise ValidationError("That file is only pretending to be a PDF.")
    elif not magic_ok and not ext_ok:
        raise ValidationError("That is not a PDF file.")

# it takes only a few seconds to join hundreds of pages
def joined_pdfs(inputs):
    """Returns url to cached union of the inputs, generating one if not available.
    Takes an absolute path to pdf as inputs."""
    path = JOIN_PATH + '%i.pdf' % abs(hash(tuple(inputs)))
    output = settings.MEDIA_ROOT + path
    url = settings.MEDIA_URL + path
    if exists(output):
        return url
    inputs = "'" + "' '".join(inputs) + "'"
    if not exists(dirname(output)):
        os.makedirs(dirname(output))
    os.system('pdftk %s cat output %s' % (inputs, output))
    return url

# Warning: This is very slow. Do not ever feed it multi-page pdfs.
def __imagemagick_t(input, output, size):
    """Imagemagick backend for thumbnailing a PDF."""
    pdf = PythonMagick.Image(input)
    scale = size / float(max(pdf.height(), pdf.width()))
    pdf.scale('%ix%i' % (pdf.size().width()*scale, pdf.size().height()*scale))
    pdf.write(output)
    return True

def __evince_t(input, output, size):
    """Evince backend for thumbnailing a PDF."""
    if os.system("evince-thumbnailer -s %i %s %s" % (size,input,output)):
        return False
    image = Image.open(output) # resize AGAIN to produce consistent sizes
    image.thumbnail((size,size), Image.ANTIALIAS)
    image.save(output, "PNG")
    return True

def pdf_to_thumbnail(input, size, abort=False):
    """Returns url to cached thumbnail, generating one if not available.
    Takes an absolute path to a pdf as input."""
    suffix = '@%i.png' % size
    path = THUMBS_PATH + basename(input[0:-4] + suffix)
    output = settings.MEDIA_ROOT + path
    url = settings.MEDIA_URL + path
    if exists(output):
        return url
    if not exists(dirname(output)):
        os.makedirs(dirname(output))
    try:
        __evince_t(input, output, size) or __imagemagick_t(input, output, size)
    except Exception:
        if not abort:
            return pdf_to_thumbnail(STOCK_FAILED_PAGE, size, True)
    return url
