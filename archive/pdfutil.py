#!/usr/bin/env python
import PythonMagick
import Image
from nexus import settings
from os.path import basename, dirname, exists
from django.core.validators import ValidationError
import os

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
    """Returns url to cached union of the inputs, generating one if not available."""
    path = 'joins/' + '%i.pdf' % abs(tuple(inputs).__hash__())
    output = settings.MEDIA_ROOT + path
    inputs = "'" + "' '".join([settings.MEDIA_ROOT + i for i in inputs]) + "'"
    if not exists(dirname(output)):
        os.mkdir(dirname(output))
    if not exists(output):
        os.system('pdftk %s cat output %s' % (inputs, output))
    return settings.MEDIA_URL + path

def pdf_to_thumbnail(input, size):
    """Returns url to cached thumbnail, generating one if not available."""
    input = settings.MEDIA_ROOT + input
    suffix = '@%i.png' % size
    path = 'thumbs/' + basename(input[0:-4] + suffix)
    output = settings.MEDIA_ROOT + path
    if not exists(dirname(output)):
        os.mkdir(dirname(output))
    if not exists(output):
        __evince_t(input, output, size) or __imagemagick_t(input, output, size)
    return settings.MEDIA_URL + path

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
