import re
from hashlib import md5
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

# taken fron django snippet #29
def slugify(inStr):
    removelist = ["a", "an", "as", "at", "before", "but", "by", "for","from","is", "in", "into", "like", "of", "off", "on", "onto","per","since", "than", "the", "this", "that", "to", "up", "via","with"];
    for a in removelist:
        aslug = re.sub(r'\b'+a+r'\b','',inStr)
    aslug = re.sub('[^\w\s-]', '', aslug).strip().lower()
    aslug = re.sub('\s+', '-', aslug)
    return aslug[:20]

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
    hash = models.TextField(blank=True, null=True, editable=False)

    def save(self):
        self.hash = md5(file(self.image.path).read()).hexdigest()
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

class ImageAdminForm(forms.ModelForm):
    def clean_image(self):
        img = self.cleaned_data['image']
        hash = md5(img.read()).hexdigest()
        query = Image.objects.filter(hash=hash).exclude(id=self.instance.id)
        if query.count() > 0:
            raise forms.ValidationError('Image already uploaded as "%s"' % query[0])
        return img
    
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
    form = ImageAdminForm

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
    slug = models.SlugField(max_length=20, unique=True, blank=True)
    snippet = models.CharField(max_length=600, blank=True, null=True)
    fulltext = models.TextField(blank=True, help_text="""<span style="color: green; 9pt; font-weight: bold;">NOTE: </span>It's no longer necessary to insert images like [[this]]. In most cases they will be automatically added with suitable formatting.""")
    date = models.DateField(help_text="Articles from the future will not be shown.")
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    image_centric = models.BooleanField(help_text="Displays images more prominently than text.")
    never_published = models.BooleanField(default=False, help_text="Disassociates article from any printed publication.")
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
            fulltext = self.cleaned_data.get('fulltext','')
            if not re.search(r'\[\[[a-z:]*%s]]' % image.slug, fulltext):
                self.cleaned_data['fulltext'] = '[[auto:' + autoclass(image, self.cleaned_data['tags'], self.cleaned_data['image_centric']) + image.slug + ']]\r\n' + fulltext
            elif re.search(r'\[\[auto:[a-z:]*%s]]' % image.slug, fulltext):
                self.cleaned_data['fulltext'] = re.sub(r'\[\[auto:[a-z:]*%s]]' % image.slug, '[[auto:' + autoclass(image, self.cleaned_data['tags'], self.cleaned_data['image_centric']) + image.slug + ']]', fulltext)
        return self.cleaned_data['images']

    def clean_tags(self):
        order = self.cleaned_data.get('order')
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

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            title = self.cleaned_data.get('title')
            if title:
                slug = slugify(title)
        return slug

    def clean_printed(self):
        online = self.cleaned_data['never_published']
        p = self.cleaned_data['printed']
        d = self.cleaned_data['date']
        if not d:
            return p # let other validators handle it
        if online:
            p = None
        else:
            try:
                p = Issue.objects.get(date=self.cleaned_data['date'])
            except Issue.DoesNotExist:
                raise forms.ValidationError("No issue found for %s. Change the article 'date' to something listed here. If this article was not published check 'never published'." % self.cleaned_data['date'])
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
    filter_horizontal = ('authors', 'tags', 'images')
    fieldsets = (
        (None, {
            'fields': ('title', 'fulltext', 'date', 'authors', 'tags', 'images')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('slug', 'snippet', 'image_centric', 'never_published', 'custom_template', 'order', 'printed')
        }),
    )


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
    date = models.DateField(unique=True)
    cover_page = models.BooleanField("Set as cover page", default=False)

    def __str__(self):
        return "/static/%s" % self.slug

    class Meta:
        ordering = ['-date']

class StaticAdminForm(forms.ModelForm):
    def clean_cover_page(self):
        if self.cleaned_data.get('cover_page'):
            for page in StaticPage.objects.filter(cover_page=True).exclude(id=self.instance.id):
                page.cover_page = False
                page.save()
        return self.cleaned_data.get('cover_page')


class StaticAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    form = StaticAdminForm
    def url(obj):
        return str(obj)
    list_display = (url, 'date', 'cover_page')

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
    start_date = models.DateField(default=date.today())
    stop_date = models.DateField(default=date.today())

    def total_votes(self):
        return sum([c.count for c in self.choice_set.all()])

    def days(self):
        days = (self.stop_date - self.start_date).days + 1
        return '%i day%s' % (days, 's' if days > 1 else '')

    def active(self):
        return self.stop_date >= date.today()
    active.boolean = True

    def __str__(self):
        return self.question

    class Meta:
        ordering = ('-stop_date', 'id')

class PollAdminForm(forms.ModelForm):
    def clean_stop_date(self):
        if self.cleaned_data['start_date'] > self.cleaned_data['stop_date']:
            raise forms.ValidationError("Stop date must be after or the same as the start date.")
        return self.cleaned_data['stop_date']

class PollAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    form = PollAdminForm
    def choices(obj):
        return ', '.join([str(c) for c in obj.choice_set.all()])
    list_display = ('question', choices, 'active')
