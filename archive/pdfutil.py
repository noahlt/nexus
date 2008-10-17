import Image
from django.conf import settings
from os.path import basename, dirname, exists, getmtime
from os import makedirs, remove, devnull
from django.forms import ValidationError
from subprocess import call

JOIN_PATH = 'cache/pdf_joins/'
THUMBS_PATH = 'cache/pdf_thumbs/'
BURST_PATH = 'pdf_burst/'

# This is only 2-3x slower than evince for short pdfs.
# However, do not ***EVER*** feed it multi-page pdfs if you fear the OOM killer.
def __imagemagick_thumbnailer(input, output, size):
    """Imagemagick backend for thumbnailing a PDF."""
    input, output = input.encode(), output.encode() # c++ signatures hate unicode
    import PythonMagick
    pdf = PythonMagick.Image(input)
    scale = size / float(max(pdf.size().height(), pdf.size().width()))
    pdf.scale('%ix%i' % (pdf.size().width()*scale, pdf.size().height()*scale))
    pdf.write(output)

def __evince_thumbnailer(input, output, size):
    """Evince backend for thumbnailing a PDF."""
    call(('evince-thumbnailer', '-s', str(size), input, output))
    image = Image.open(output) # resize AGAIN to produce consistent sizes
    image.thumbnail((size,size), Image.ANTIALIAS)
    image.save(output, 'PNG')

try:
    call(('evince-thumbnailer', devnull, devnull))
    __thumbnail_backend = __evince_thumbnailer
except OSError:
    __thumbnail_backend = __imagemagick_thumbnailer

def validate_pdf(in_memory_uploaded_file):
    ext_ok = in_memory_uploaded_file.name.endswith('.pdf')
    magic_ok = in_memory_uploaded_file.chunks().next().startswith('%PDF')
    if magic_ok and not ext_ok:
        raise ValidationError("Please rename that file so it has a .pdf extension")
    if not magic_ok and ext_ok:
        raise ValidationError("That file is only pretending to be a PDF.")
    elif not magic_ok and not ext_ok:
        raise ValidationError("That is not a PDF file.")

def burst_pdf(input):
    """Creates new files for all input pages and returns their relative paths.
    Takes an absolute path to a pdf as input."""
    output_dir = settings.MEDIA_ROOT + BURST_PATH
    if not exists(output_dir):
        makedirs(output_dir)
    base = basename(input)[0:-4]
    output_format = '%s+%%03d.pdf' % (output_dir + base)
    call(('pdftk', input, 'burst', 'output', output_format))
    try: # pdftk insists on spitting this out
        remove('doc_data.txt')
    except OSError:
        pass
    results = []
    i = 1 # go and count up what pdftk did:
    while True:
        path = '%s+%03d.pdf' % (base, i)
        if exists(output_dir + path):
            results.append(BURST_PATH + path)
        else:
            break
        i += 1
    return results

# it takes only a few seconds to join hundreds of pages
def joined_pdfs(input_models):
    """Returns url to cached union of the inputs, generating one if not available.
    Takes a list of PDF models as input."""
    maxtime = 0
    for model in input_models:
        time = getmtime(model.pdf.path)
        if time > maxtime:
            maxtime = time
    path = JOIN_PATH + '%s.pdf' % maxtime
    output = settings.MEDIA_ROOT + path
    url = settings.MEDIA_URL + path
    if exists(output) and getmtime(output) > maxtime:
        return url
    if not exists(dirname(output)):
        makedirs(dirname(output))
    inputs = [model.pdf.path for model in input_models]
    try:
        call(['pdftk'] + inputs + ['cat', 'output', output])
    except EnvironmentError:
        pass
    return url

def pdf_to_thumbnail(input, size):
    """Returns url to cached thumbnail, generating one if not available.
    Takes an absolute path to a pdf as input.
    Tries very hard to return something sane."""
    suffix = '@%i.png' % size
    name = basename(input)[0:-4]
    path = THUMBS_PATH + name + suffix
    output = settings.MEDIA_ROOT + path
    url = settings.MEDIA_URL + path
    if exists(output) and getmtime(output) > getmtime(input):
        return url
    if not exists(dirname(output)):
        makedirs(dirname(output))
    try:
        __thumbnail_backend(input, output, size)
    except EnvironmentError:
        pass
    return url
