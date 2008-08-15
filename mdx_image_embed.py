import markdown
from nexus.cover.models import Image

class FakePixmap():
    url = 'broken'

class FakeAuthors():
    def all(self):
        return []

class FakeImage():
    caption = "This is not a valid image."
    image = FakePixmap()
    authors = FakeAuthors()
    date = "????-??-??"

class ImageEmbedPattern(markdown.Pattern):
    def handleMatch(self, m, doc):
        div = doc.createElement('div')
        div.setAttribute('class', 'image')
        caption = doc.createElement('span')
        caption.setAttribute('class', 'caption')
        img = doc.createElement('img')
        try:
            obj = Image.objects.get(slug=m.group(2))
        except:
            obj = FakeImage() # XXX this is silly
        img.setAttribute('src', obj.image.url)
        caption.appendChild(doc.createTextNode(obj.caption))
        div.appendChild(img)
        authors = ', '.join([str(author) for author in obj.authors.all()])
        span = doc.createElement('span')
        span.setAttribute('class', 'author')
        span.appendChild(doc.createTextNode(authors))
        div.appendChild(span)
        div.appendChild(caption)
        return div

class ImageEmbedExtension(markdown.Extension):
    def __init__(self, configs):
        self.config = {}
        for key, value in configs :
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        md.img_config = self.config
        IMAGE_EMBED_RE = r'\[\[(.*?)]]'
        IMAGE_EMBED_PATTERN = ImageEmbedPattern(IMAGE_EMBED_RE)
        IMAGE_EMBED_PATTERN.md = md
        md.inlinePatterns.append(IMAGE_EMBED_PATTERN)

def makeExtension(configs=None):
    return ImageEmbedExtension(configs=configs)
