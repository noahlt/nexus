from django import forms
from django.db import models
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from imageutil import resize, THUMB_MAX_SIZE, ARTICLE_MAX_SIZE

IMAGE_PATH = 'image_orig/'

class Author(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    year = models.PositiveSmallIntegerField()

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

class Tag(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class Image(models.Model):
    image = models.ImageField(upload_to='image_orig/')
    caption = models.TextField()
    slug = models.CharField(primary_key=True, max_length=20,
        help_text="You can embed images in articles as [[slug]]")
    authors = models.ManyToManyField(Author)
    date = models.DateField()
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
    
class ImageAdminForm(forms.ModelForm):
    # FIXME manual validation... since primary_key=True doesn't validate uniqueness?
    def clean_slug(self):
        if 'slug' not in self.changed_data:
            return self.cleaned_data['slug']
        try:
            date = Image.objects.get(slug=self.cleaned_data['slug'])
        except ObjectDoesNotExist:
            return self.cleaned_data['slug']
        raise forms.ValidationError("That slug is already taken.")

class ImageAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('caption',)}
    form = ImageAdminForm

class Article(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=20)
    snippet = models.CharField(max_length=600)
    fulltext = models.TextField()
    date = models.DateField()
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    published = models.BooleanField()
    images = models.ManyToManyField(Image, blank=True)

    # Article tags are stored (in slug form) as the classes of the li's that
    # wrap articles, so the js doesn't have to look up article tags itself.
    @property
    def tagclasses(self):
        return ' '.join(tag.slug for tag in self.tags.all())
    
    def __str__(self):
        return self.title + ' [ ' + ' '.join(str(tag) for tag in self.tags.all()) + ' ] '

    class Meta:
        ordering = ['title']

class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    
