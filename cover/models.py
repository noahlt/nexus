import re
from datetime import date
from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import models
from imageutil import *
from nexus.archive.models import Issue, ignore_errors

NEWLINE = re.compile('([^\n])\n([^\n])')
PARAGRAPH = re.compile(r'\n[A-Z][^\n]+\n')
IMAGE_PATH = 'image_orig/'
L1, L2, L3 = (1,2,3)
ARTICLE_TEMPLATE = """{% extends "article.html" %}
You can modify blocks by adding text/html around the {{ block.super }} part.
Most anything outside the block tags will be ignored.

{% block article_title %}
{{ block.super }}
{% endblock %}

{% block article_subtitle %}
{{ block.super }}
{% endblock %}

{% block content %}
{{ block.super }}
{% endblock %}

{% block extra %}
{{ block.super }}
{% endblock %}"""

class Title(models.Model):
    title = models.CharField(max_length=30, help_text="Staff Writer, Photographer, etc.")
    plural_form = models.CharField(max_length=33, blank=True, null=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return "%s" % self.title

    class Meta:
        ordering = ('order', 'id')

class TitleAdmin(admin.ModelAdmin):
    def active_authors(obj):
        return ', '.join([str(x) for x in obj.author_set.all() if not x.retired])
    list_display = ('title', 'order', active_authors)

class Author(models.Model):
    name = models.CharField(max_length=75)
    slug = models.SlugField(max_length=30, unique=True)
    bio = models.TextField(blank=True, null=True)
    title = models.ForeignKey(Title, blank=True, null=True, help_text="Leave blank if unknown or to exclude author from staff page.")
    year = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Year of graduation, if applicable.")
    retired = models.BooleanField(help_text="Adds 'former' to title; hides author from staff list.")
    nexus_staff = models.BooleanField(help_text="Allows author to show up in staff list if not retired.")
    grouping = models.ManyToManyField('self', blank=True, null=True,
        help_text="Associates author with group and vice versa.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('retired', 'name', 'id')

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
        return ', '.join([group.name for group in obj.grouping.all()])
    list_display = ('name', 'year', 'title', grouped_with, num_articles, num_images, 'nexus_staff')
    list_filter = ('title', 'year', 'retired')
    search_fields = ('name',)
    filter_horizontal = ('grouping',)

class Tag(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30, unique=True)
    order = models.IntegerField(default=0)
    article_priority = models.FloatField(default=0)
    type = models.IntegerField(choices=((L1, "Bottom"),(L2, "Middle"), (L3, "Top")), default=L1)
    article_regex = models.CharField(max_length=50, blank=True, null=True)
    article_regex_sub = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-type', 'order', 'name', 'id']

class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    def num_articles(obj):
        return str(obj.article_set.count())
    def num_images(obj):
        return str(obj.image_set.count())
    def modifies_article_title(obj):
        return bool(obj.article_regex and obj.article_regex_sub)
    modifies_article_title.boolean = True
    list_display = ('name', 'type', modifies_article_title, 'article_priority', 'order', num_articles, num_images)

class Image(models.Model):
    image = models.ImageField(upload_to='image_orig/')
    caption = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=20, unique=True,
        help_text="You can embed images in articles as [[slug]]")
    authors = models.ManyToManyField(Author)
    date = models.DateField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    lossless = models.BooleanField("Use lossless compression", help_text="For detailed or computer generated images. Will result in larger file sizes for photographic images.", default=False)
    priority = models.IntegerField("Preview priority", default=0)

    def save(self):
        super(Image, self).save()
        self.thumbnail_size()
        self.small_size()
        self.article_size()

    @ignore_errors
    def thumbnail_size(self):
        return resize(self.image.path, THUMB_MAX_SIZE, self.lossless)

    @ignore_errors
    def small_size(self):
        return resize(self.image.path, SMALL_MAX_SIZE, self.lossless)

    @ignore_errors
    def article_size(self):
        return resize(self.image.path, ARTICLE_MAX_SIZE, self.lossless)

    class Meta:
        ordering = ['-priority', 'id']

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
    filter_horizontal = ('authors', 'tags')

class CustomArticleTemplate(models.Model):
    name = models.CharField(max_length=50)
    template = models.TextField(
        default=ARTICLE_TEMPLATE)

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
    fulltext = models.TextField(blank=True)
    date = models.DateField(help_text="Articles from the future will not be shown.")
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    image_centric = models.BooleanField(help_text="Use for cartoons or photo galleries.")
    never_published = models.BooleanField(default=False, help_text="Here to make sure you don't forget the 'printed' field.")
    printed = models.ForeignKey(Issue, blank=True, null=True)
    images = models.ManyToManyField(Image, blank=True)
    custom_template = models.ForeignKey(CustomArticleTemplate, blank=True, null=True)
    order = models.FloatField(blank=True, null=True)

    def auto_snippet(self):
        if self.snippet:
            return self.snippet
        match = PARAGRAPH.search('\n' + self.fulltext + '\n')
        return match.group()[1:-1] if match else ''

    def auto_title(self):
        # filter() doesn't seem to work with __isnull=False !?
        for tag in [ tag for tag in self.tags.all() if tag.article_regex and tag.article_regex_sub ]:
            try:
                return re.compile(tag.article_regex).sub(tag.article_regex_sub, self.title)
            except Exception, e:
                return '%s<br><span class="type" style="font-size:8pt;color:red">Exception applying tag regex: %s</span>' % (self.title, e)
        return self.title

    def text(self):
        return NEWLINE.sub(r'\1  \n\2', self.fulltext)

    def current(self):
        return self.date <= date.today()

    def __str__(self):
        return "%s" % self.title

    class Meta:
        ordering = ['-date', '-order', '-id']

class ArticleAdminForm(forms.ModelForm):

    def clean_images(self):
        for image in self.cleaned_data['images']:
            if not re.search(r'\[\[[a-z:]*%s]]' % image.slug, self.cleaned_data.get('fulltext','')):
                self.cleaned_data['fulltext'] = '[[' + autoclass(image, self.cleaned_data['tags'], self.cleaned_data['image_centric']) + image.slug + ']]\r\n' + self.cleaned_data.get('fulltext','')
        return self.cleaned_data['images']

    def clean_tags(self):
        order = self.cleaned_data.get('order', None)
        if order is None:
            order = 0
            for tag in self.cleaned_data['tags']:
                if tag.article_priority > order:
                    order = tag.article_priority
        self.cleaned_data['order'] = order
        return self.cleaned_data['tags']

    def clean_title(self):
        try:
            self.cleaned_data['title'].encode()
        except:
            return self.cleaned_data['title'].encode('ascii', 'xmlcharrefreplace')
        return self.cleaned_data['title']

    def clean_printed(self):
        p = self.cleaned_data['printed']
        if not p and not self.cleaned_data['never_published']:
            raise forms.ValidationError("Check 'never published' if this article was never printed.")
        if p and self.cleaned_data['never_published']:
            raise forms.ValidationError("Uncheck 'never published' if this article was printed.")
        if p and p.date != self.cleaned_data['date']:
            raise forms.ValidationError("Printed date disagrees with publication date.")
        return p

class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    prepopulated_fields = {'slug': ('title',)}
    def tags(obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    def visible(obj):
        return obj.current()
    def template(obj):
        return obj.custom_template if obj.custom_template else ''
    visible.boolean = True
    list_display = ('title', 'printed', tags, visible, 'order')
    list_filter = ('date', 'printed', 'authors')
    search_fields = ('title', 'slug', 'date')
    filter_horizontal = ('authors','tags','images')

class InfoPage(models.Model):
    title = models.CharField(max_length=100)
    link_name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20, unique=True,
        help_text="Note: choosing 'staff' will create a page auto-filled by current staff.")
    order = models.IntegerField(default=0, help_text="Order of display in footer.")
    show_in_footer = models.BooleanField(default=True)
    fulltext = models.TextField(blank=True, null=True)

    def text(self):
        return NEWLINE.sub(r'\1  \n\2', self.fulltext)

    def __str__(self):
        return "/info/%s -> %s" % (self.link_name, self.title)

    class Meta:
        ordering = ['order', 'id']

class InfoPageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('link_name',)}
    list_display = ('title', 'link_name', 'order')

class StaticPage(models.Model):
    title = models.CharField(max_length=100)
    slug = models.CharField(max_length=20)
    html = models.TextField()

    def __str__(self):
        return "/static/%s" % self.slug

class StaticAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}

class SideBarLink(models.Model):
    link_name = models.CharField(max_length=100);
    link_target = models.CharField(max_length=300);
    order = models.IntegerField(default=0, help_text="Order of display in sidebar.")

    def external(self):
        return self.link_target[0] != '/'

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return "%s -> %s" % (self.link_name, self.link_target)

class SideBarLinkAdmin(admin.ModelAdmin):
    list_display = ('link_name', 'link_target', 'order')

class Choice(models.Model):
    count = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('Poll')

    def __str__(self):
        return "%s: %i" % (self.name, self.count)

    class Meta:
        ordering = ('order', 'id')

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 5

class Poll(models.Model):
    question = models.CharField(max_length=300)
    active = models.BooleanField(default=True)
    date = models.DateField(default=date.today())

    def total_votes(self):
        return sum([c.count for c in self.choice_set.all()])

    def __str__(self):
        return self.question

    class Meta:
        ordering = ('-active', 'date', 'id')

class Voter(models.Model):
    ip = models.CharField(max_length=30)
    polls = models.ManyToManyField(Poll, blank=True, null=True)

class PollAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    def choices(obj):
        return ', '.join([str(c) for c in obj.choice_set.all()])
    list_display = ('question', choices, 'active')
