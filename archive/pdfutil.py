#!/usr/bin/env python
import PythonMagick
import Image
from nexus import settings
from os.path import basename, dirname, exists
import os

def pdf_to_thumbnail(input, size=128):
    input = settings.MEDIA_ROOT + input.encode()
    suffix = '-%i.png' % size
    output = settings.MEDIA_ROOT + 'thumbs/' + basename(input[0:-4] + suffix)
    if not exists(dirname(output)):
        os.mkdir(dirname(output))
    if not exists(output):
        if __evince_thumbnail(input, output, size):
            __imagemagick_thumbnail(input, output, size)
    return settings.MEDIA_URL + 'thumbs/' + basename(output)

def __imagemagick_thumbnail(input, output, size):
    pdf = PythonMagick.Image(input)
    pdf.write(output)
    image = Image.open(output)
    image.thumbnail((size,size), Image.ANTIALIAS)
    image.save(output, "PNG")

def __evince_thumbnail(input, output, size):
    os.system("evince-thumbnailer -s %i %s %s" % (size,input,output)) 
    image = Image.open(output) # resize AGAIN to produce consistent sizes
    image.thumbnail((size,size), Image.ANTIALIAS)
    image.save(output, "PNG")
