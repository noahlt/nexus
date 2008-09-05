from django.db import models
from django.contrib import admin
from imageutil import resize, THUMB_MAX_SIZE, ARTICLE_MAX_SIZE
from nexus.archive.models import Issue

IMAGE_PATH = 'image_orig/'

class Title(models.Model):
    title = models.CharField(max_length=30, help_text="Staff Writer, Photographer, etc.")

    def __str__(self):
        return "%s" % self.title

class TitleAdmin(admin.ModelAdmin):
    def active_authors(obj):
        return ', '.join([str(x) for x in obj.author_set.all() if not x.retired])
    list_display = ('title', active_authors)

class Author(models.Model):
    name = models.CharField(max_length=75)
    slug = models.SlugField(max_length=30, unique=True)
    title = models.ForeignKey(Title, blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True,
        help_text="Year of graduation, if applicable.")
    retired = models.BooleanField(help_text="Adds 'former' to title; hides author from staff list.")
    nexus_staff = models.BooleanField(help_text="Allows author to show up in staff list if not retired.")
    subauthors = models.ManyToManyField('self', blank=True, null=True,
        help_text="Applicable if the 'author' is really a group of people.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('retired', 'name',)

class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    def num_articles(obj):
        return str(obj.article_set.count())
    def num_images(obj):
        return str(obj.image_set.count())
    def groups(obj):
        try:
            return ', '.join([group.name for group in obj.subauthors.all()])
        except:
            return None
    list_display = ('name', 'year', 'title', groups, num_articles, num_images)
    list_filter = ('title', 'year', 'retired')
    search_fields = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'title', 'year', 'retired', 'nexus_staff')
        }),
        ('Group relations', {
            'classes': ('collapse',),
            'fields': ('subauthors',)
        }),
    )

class Tag(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    def num_articles(obj):
        return str(obj.article_set.count())
    def num_images(obj):
        return str(obj.image_set.count())
    list_display = ('name', num_articles, num_images)

class Image(models.Model):
    image = models.ImageField(upload_to='image_orig/')
    caption = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=20, unique=True,
        help_text="You can embed images in articles as [[slug]]")
    authors = models.ManyToManyField(Author)
    date = models.DateField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def save(self):
        super(Image, self).save()
        self.thumbnail_size()
        self.article_size()

    def thumbnail_size(self):
        return resize(self.image.path, THUMB_MAX_SIZE)

    def article_size(self):
        return resize(self.image.path, ARTICLE_MAX_SIZE)

    def __str__(self):
        return self.slug
    
class ImageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('caption',)}
    def tags(obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    def article_list(obj):
        return ', '.join([str(i) for i in obj.article_set.all()])
    def author(obj):
        return ', '.join([str(i) for i in obj.authors.all()])
    list_filter = ('date', 'tags')
    list_display = ('slug', author, tags, article_list)

class Article(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=20, unique=True)
    snippet = models.CharField(max_length=600, blank=True, null=True)
    fulltext = models.TextField()
    date = models.DateField()
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    published = models.BooleanField()
    image_centric = models.BooleanField()
    printed = models.ForeignKey(Issue, blank=True, null=True)
    images = models.ManyToManyField(Image, blank=True)

    # Article tags are stored (in slug form) as the classes of the li's that
    # wrap articles, so the js doesn't have to look up article tags itself.
    @property
    def tagclasses(self):
        return ' '.join(tag.slug for tag in self.tags.all())
    
    def __str__(self):
        return "%s" % self.title

    class Meta:
        ordering = ['-date', '-printed']

class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    def tags(obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    def author(obj):
        return ', '.join([str(i) for i in obj.authors.all()])
    list_display = ('title', author, tags, 'printed')
    list_filter = ('date', 'printed', 'date', 'tags')
    search_fields = ('title',)

class InfoPage(models.Model):
    title = models.CharField(max_length=100)
    link_name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20, unique=True,
        help_text="Note: choosing 'staff' will create a page auto-filled by current staff.")
    order = models.IntegerField(default=0, help_text="Order of display in footer. Set to -1 to hide from footer.")
    fulltext = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s -> %s" % (self.link_name, self.title)

    class Meta:
        ordering = ['order']

class InfoPageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('link_name',)}
    list_display = ('title', 'link_name', 'order')
