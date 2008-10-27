import Image
from django.conf import settings
from os.path import basename, dirname, exists, getmtime
from os import makedirs, remove, devnull
from django.forms import ValidationError
from subprocess import call, PIPE

JOIN_PATH = 'cache/pdf_joins/'
THUMBS_PATH = 'cache/pdf_thumbs/'
BURST_PATH = 'pdf_burst/'

def nameof(path):
    """Returns file basename stripped of file extension."""
    base = basename(path)
    index = base.rfind('.')
    return base[:index] if index > 0 else base

def mktemp(x):
    return dirname(x) + "/swp-" + basename(x)

# This is only 2-3x slower than evince for short pdfs.
# However, do not ***EVER*** feed it multi-page pdfs if you fear the OOM killer.
def __pythonmagick_thumbnailer(input, output, size):
    """Imagemagick backend for thumbnailing a PDF."""
    input, output = input.encode(), output.encode() # c++ signatures hate unicode
    pdf = PythonMagick.Image(input)
    scale = size / float(pdf.size().width())
    pdf.scale('%ix%i' % (pdf.size().width()*scale, pdf.size().height()*scale))
    pdf.write(output)

# almost identical to pythonmagick thumbnailer
def __imagemagick_thumbnailer(input, output, size):
    """Imagemagick backend for thumbnailing a PDF."""
    swap = mktemp(output)
    call(('convert', input, swap))
    image = Image.open(swap) # resize AGAIN to produce consistent sizes
    image = image.convert('RGBA')
    image.thumbnail((size,2048), Image.ANTIALIAS)
    image.save(output, 'JPEG', quality=85)
    remove(swap)

def __evince_thumbnailer(input, output, size):
    """Evince backend for thumbnailing a PDF."""
    swap = mktemp(output)
    call(('evince-thumbnailer', '-s', str(size), input, swap))
    image = Image.open(swap) # resize AGAIN to produce consistent sizes
    image = image.convert('RGBA')
    image.thumbnail((size,2048), Image.ANTIALIAS)
    image.save(output, 'JPEG', quality=85)
    remove(swap)

try:
    call(('evince-thumbnailer', devnull, devnull))
    __thumbnail_backend = __evince_thumbnailer
except OSError:
    try:
        import PythonMagick
        __thumbnail_backend = __pythonmagick_thumbnailer
    except ImportError:
        __thumbnail_backend = __imagemagick_thumbnailer

def __pdftk_burst(input, output_dir):
    base = nameof(input)
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
            results.append(output_dir + path)
        else:
            break
        i += 1
    return results

def __pypdf_burst(input, output_dir):
    # XXX avoid memory leaks
    call((dirname(__file__) + '/pypdf_burst', input, output_dir))
    results = []
    i = 1 # TODO read results from stdout instead
    base = nameof(input)
    while True:
        path = '%s+%03d.pdf' % (base, i)
        if exists(output_dir + path):
            results.append(output_dir + path)
        else:
            break
        i += 1
    return results

def __pdftk_join(inputs, output):
    try:
        call(['pdftk'] + inputs + ['cat', 'output', output])
    except EnvironmentError:
        pass

def __pypdf_join(inputs, output):
    # XXX avoid memory leaks
    call([dirname(__file__) + '/pypdf_join', output] + inputs)

try:
    call('pdftk', stdout=PIPE)
    __join_backend = __pdftk_join
    __burst_backend = __pdftk_burst
except OSError:
    __join_backend = __pypdf_join
    __burst_backend = __pypdf_burst

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
    return __burst_backend(input, output_dir)

# it takes only a few seconds to join hundreds of pages
def joined_pdfs(input_models, id):
    """Returns url to cached union of the inputs, generating one if not available.
    Takes a list of PDF models as input."""
    maxtime = 0
    for model in input_models:
        time = getmtime(model.pdf.path)
        if time > maxtime:
            maxtime = time
    path = JOIN_PATH + '%s.pdf' % id
    output = settings.MEDIA_ROOT + path
    url = settings.MEDIA_URL + path
    if exists(output) and getmtime(output) > maxtime:
        return url
    if not exists(dirname(output)):
        makedirs(dirname(output))
    inputs = [model.pdf.path for model in input_models]
    __join_backend(inputs, output)
    return url

def pdf_to_thumbnail(input, size):
    """Returns url to cached thumbnail, generating one if not available.
    Takes an absolute path to a pdf as input.
    Tries very hard to return something sane."""
    suffix = '@%i.jpg' % size
    name = nameof(input)
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
