from datetime import date
from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import models
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
    title = models.ForeignKey(Title, blank=True, null=True, help_text="Leave blank if unknown or to exclude author from staff page.")
    year = models.PositiveSmallIntegerField(blank=True, null=True,
        help_text="Year of graduation, if applicable.")
    retired = models.BooleanField(help_text="Adds 'former' to title; hides author from staff list.")
    nexus_staff = models.BooleanField(help_text="Allows author to show up in staff list if not retired.")
    grouping = models.ManyToManyField('self', blank=True, null=True,
        help_text="Associates author with group and vice versa.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('retired', 'name',)

class AuthorAdminForm(forms.ModelForm):
    def clean_grouping(self):
        if self.instance in self.cleaned_data['grouping']:
            raise forms.ValidationError("Cannot be subset of '%s'." % self.instance)
        return self.cleaned_data['grouping']

class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    form = AuthorAdminForm
    def num_articles(obj):
        return str(obj.article_set.count())
    def num_images(obj):
        return str(obj.image_set.count())
    def grouped_with(obj):
        try:
            return ', '.join([group.name for group in obj.grouping.all()])
        except:
            return None
    list_display = ('name', 'year', 'title', grouped_with, num_articles, num_images, 'nexus_staff')
    list_filter = ('title', 'year', 'retired')
    search_fields = ('name',)

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
    priority = models.IntegerField("Preview priority", default=0)

    def save(self):
        super(Image, self).save()
        self.thumbnail_size()
        self.article_size()

    def thumbnail_size(self):
        return resize(self.image.path, THUMB_MAX_SIZE)

    def article_size(self):
        return resize(self.image.path, ARTICLE_MAX_SIZE)

    class Meta:
        ordering = ['-priority']

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
    search_fields = ('slug', 'caption')

class CustomArticleTemplate(models.Model):
    name = models.CharField(max_length=50)
    template = models.TextField(
        default=open(settings.MEDIA_ROOT + 'article-extension-example.html').read())

    def __str__(self):
        return self.name

class CustomArticleTemplateAdmin(admin.ModelAdmin):
    def article_count(obj):
        return obj.article_set.count()
    list_display = ('name', article_count)

class Article(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=20, unique=True)
    snippet = models.CharField(max_length=600, blank=True, null=True)
    fulltext = models.TextField()
    date = models.DateField(help_text="Articles from the future will not be shown.")
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    image_centric = models.BooleanField(help_text="Shows a large image preview.")
    printed = models.ForeignKey(Issue, blank=True, null=True)
    images = models.ManyToManyField(Image, blank=True)
    custom_template = models.ForeignKey(
        CustomArticleTemplate, blank=True, null=True)

    def current(self):
        return self.date <= date.today()

    def __str__(self):
        return "%s" % self.title

    class Meta:
        ordering = ['-date', '-printed']

class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    def tags(obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    def visible(obj):
        return obj.current()
    def url(obj):
        if obj.current():
            return "/%s/%s" % (obj.date.strftime("%Y/%m"), obj.slug)
        else:
            return "/future/%s" % obj.slug
    def template(obj):
        return obj.custom_template if obj.custom_template else ''
    visible.boolean = True
    list_display = ('title', tags, visible, url, template)
    list_filter = ('date', 'printed', 'authors')
    search_fields = ('title', 'snippet', 'date')

class InfoPage(models.Model):
    title = models.CharField(max_length=100)
    link_name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20, unique=True,
        help_text="Note: choosing 'staff' will create a page auto-filled by current staff.")
    order = models.IntegerField(default=0, help_text="Order of display in footer.")
    show_in_footer = models.BooleanField(default=True)
    fulltext = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s -> %s" % (self.link_name, self.title)

    class Meta:
        ordering = ['order']

class InfoPageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('link_name',)}
    list_display = ('title', 'link_name', 'order')
