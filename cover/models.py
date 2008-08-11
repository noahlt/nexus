from django.db import models
from django.contrib import admin

# Create your models here.

class Author(models.Model):
    first_name = models.CharField(max_length=30)
    last_name  = models.CharField(max_length=40)
    year = models.PositiveSmallIntegerField()

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)
    
class Tag(models.Model):
    name = models.CharField(max_length = 30)

    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=20)
    snippet = models.CharField(max_length=600)
    fulltext = models.TextField()
    date = models.DateField()
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    published = models.BooleanField()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']

class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
