from django.db import models
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import admin
from imageutil import resize, THUMB_MAX_SIZE, ARTICLE_MAX_SIZE
from nexus.archive.models import Issue

IMAGE_PATH = 'image_orig/'

class ImageAdminForm(forms.ModelForm):
    # XXX manual validation find why unique=True doesn't work
    def clean_slug(self):
        if 'slug' not in self.changed_data:
            return self.cleaned_data['slug']
        try:
            Image.objects.get(slug=self.cleaned_data['slug'])
        except ObjectDoesNotExist:
            return self.cleaned_data['slug']
        raise forms.ValidationError("That slug is already taken.")

class TagAdminForm(forms.ModelForm):
    # XXX manual validation find why unique=True doesn't work
    def clean_slug(self):
        if 'slug' not in self.changed_data:
            return self.cleaned_data['slug']
        try:
            Tag.objects.get(slug=self.cleaned_data['slug'])
        except ObjectDoesNotExist:
            return self.cleaned_data['slug']
        raise forms.ValidationError("That slug is already taken.")

class TitleAdminForm(forms.ModelForm):
    # XXX manual validation find why unique=True doesn't work
    def clean_slug(self):
        if 'slug' not in self.changed_data:
            return self.cleaned_data['slug']
        try:
            Title.objects.get(slug=self.cleaned_data['slug'])
        except ObjectDoesNotExist:
            return self.cleaned_data['slug']
        raise forms.ValidationError("That slug is already taken.")

class AuthorAdminForm(forms.ModelForm):
    # XXX manual validation find why unique=True doesn't work
    def clean_slug(self):
        if 'slug' not in self.changed_data:
            return self.cleaned_data['slug']
        try:
            Author.objects.get(slug=self.cleaned_data['slug'])
        except ObjectDoesNotExist:
            return self.cleaned_data['slug']
        raise forms.ValidationError("That slug is already taken.")

class ArticleAdminForm(forms.ModelForm):
    # XXX manual validation find why unique=True doesn't work
    def clean_slug(self):
        if 'slug' not in self.changed_data:
            return self.cleaned_data['slug']
        try:
            Article.objects.get(slug=self.cleaned_data['slug'])
        except ObjectDoesNotExist:
            return self.cleaned_data['slug']
        raise forms.ValidationError("That slug is already taken.")

class Title(models.Model):
    title = models.CharField(max_length=30, help_text="Staff Writer, AP, etc.")

    def __str__(self):
        return "%s" % self.title

class TitleAdmin(admin.ModelAdmin):
    def active_authors(obj):
        return ', '.join([str(x) for x in obj.author_set.all() if not x.retired])
    form = TitleAdminForm
    list_display = ('title', active_authors)

class Author(models.Model):
    name = models.CharField(max_length=75)
    slug = models.SlugField(max_length=30, unique=True)
    title = models.ForeignKey(Title, blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True,
        help_text="Year of graduation, if applicable.")
    not_staff = models.BooleanField(help_text="Adds 'courtesy of' to photo attribution.")
    retired = models.BooleanField(help_text="Adds 'former' to title.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('not_staff', 'retired', 'name',)

class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    form = AuthorAdminForm
    def name(obj):
        return str(obj)
    def num_articles(obj):
        return str(obj.article_set.count())
    def num_images(obj):
        return str(obj.image_set.count())
    list_display = (name, 'year', 'title', num_articles, num_images)
    list_filter = ('year', 'retired', 'not_staff')

class Tag(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    form = TagAdminForm
    def num_articles(obj):
        return str(obj.article_set.count())
    def num_images(obj):
        return str(obj.image_set.count())
    list_display = ('name', num_articles, num_images)

class Image(models.Model):
    image = models.ImageField(upload_to='image_orig/')
    caption = models.TextField()
    slug = models.CharField(max_length=20, unique=True,
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
    form = ImageAdminForm
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
    snippet = models.CharField(max_length=600)
    fulltext = models.TextField()
    date = models.DateField()
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    published = models.BooleanField()
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
        ordering = ['title']

class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    form = ArticleAdminForm
    def tags(obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    def image_list(obj):
        return ', '.join([str(i) for i in obj.images.all()])
    def author(obj):
        return ', '.join([str(i) for i in obj.authors.all()])
    list_display = ('title', author, tags, image_list)
    list_filter = ('date', 'tags')
    search_fields = ('title',)
