from django import forms
from django.db import models
from django.contrib import admin

# Create your models here.

class Author(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    year = models.PositiveSmallIntegerField()

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

class Tag(models.Model):
    name = models.CharField(max_length = 30)
    slug = models.SlugField(max_length = 30)

    def __str__(self):
        return self.name

class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class Image(models.Model):
    slug = models.CharField(primary_key=True, max_length=20,
        help_text="You can embed images in articles as [[slug]]")
    caption = models.TextField()
    image = models.ImageField(upload_to="images/")
    authors = models.ManyToManyField(Author)
    date = models.DateField()

    def __str__(self):
        return self.slug
    
class ImageAdminForm(forms.ModelForm):
    # FIXME manual validation... since primary_key=True doesn't validate uniqueness?
    def clean_slug(self):
        if 'slug' not in self.changed_data:
            return self.cleaned_data['slug']
        try:
            date = Image.objects.get(slug=self.cleaned_data['slug'])
        except:
            return self.cleaned_data['slug']
        raise forms.ValidationError("That slug is already taken.")

class ImageAdmin(admin.ModelAdmin):
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
    images = models.ManyToManyField(Image)

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
    
