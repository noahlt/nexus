#!/usr/bin/env python
import Image
from nexus import settings
from os.path import basename, dirname, exists
from django.forms import ValidationError
import os

JOIN_PATH = 'cache/joins/'
THUMBS_PATH = 'cache/thumbs/'
BURST_PATH = 'pdf/'
STOCK_FAILED_PAGE = settings.MEDIA_ROOT + 'stock/FAILED_PAGE.pdf'

def validate_pdf(in_memory_uploaded_file):
    ext_ok = in_memory_uploaded_file.name.endswith('.pdf')
    try:
        magic_ok = in_memory_uploaded_file.file.startswith('%PDF')
    except Exception:
        if not ext_ok:
            raise ValidationError("That is not a PDF file.")
        return
    if magic_ok and not ext_ok:
        raise ValidationError("Please rename that file so it has a .pdf extension")
    if not magic_ok and ext_ok:
        raise ValidationError("That file is only pretending to be a PDF.")
    elif not magic_ok and not ext_ok:
        raise ValidationError("That is not a PDF file.")

def burst_pdf(input):
    """Creates new files for all input pages and returns their relative paths."""
    output_dir = settings.MEDIA_ROOT + BURST_PATH
    if not exists(output_dir):
        os.makedirs(output_dir)
    base = basename(input)[0:-4]
    os.system("pdftk '%s' burst output '%s+%%i.pdf'" % (input, output_dir + base))
    os.remove('doc_data.txt')
    results = []
    i = 1 # go and count up what pdftk did:
    while True:
        path = '%s+%i.pdf' % (base, i)
        if exists(output_dir + path):
            results.append(BURST_PATH + path)
        else:
            break
        i += 1
    if i == 2: # well, that was pointless
        path = '%s+%i.pdf' % (base, 1)
        os.remove(output_dir + path)
        return [input]
    return results

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
    os.system("pdftk %s cat output %s" % (inputs, output))
    return url

# Warning: This is very slow. Do not ever feed it multi-page pdfs.
def __imagemagick(input, output, size):
    """Imagemagick backend for thumbnailing a PDF."""
    import PythonMagick
    pdf = PythonMagick.Image(input)
    scale = size / float(max(pdf.height(), pdf.width()))
    pdf.scale('%ix%i' % (pdf.size().width()*scale, pdf.size().height()*scale))
    pdf.write(output)

def __evince(input, output, size):
    """Evince backend for thumbnailing a PDF."""
    assert os.system("evince-thumbnailer -s %i '%s' '%s'" % (size,input,output)) == 0
    image = Image.open(output) # resize AGAIN to produce consistent sizes
    image.thumbnail((size,size), Image.ANTIALIAS)
    image.save(output, 'PNG')

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
        __evince(input, output, size)
    except AssertionError:
        __imagemagick(input, output, size)
    except Exception:
        if not abort:
            return pdf_to_thumbnail(STOCK_FAILED_PAGE, size, True)
    return url
