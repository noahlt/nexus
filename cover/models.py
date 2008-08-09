from django.db import models

# Create your models here.

class Author(models.Model):
    first_name = models.CharField(maxlength=30)
    last_name  = models.CharField(maxlength=40)
    year = models.PositiveSmallIntegerField()

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

    class Admin:
        pass
    
class Tag(models.Model):
    name = models.CharField(maxlength = 30)

    def __str__(self):
        return self.name

    class Admin:
        pass


class Article(models.Model):
    title = models.CharField(maxlength=50)
    slug = models.SlugField(maxlength=20)
    snippet = models.CharField(maxlength=600)
    fulltext = models.TextField()
    date = models.DateField()
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    published = models.BooleanField()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']

    class Admin:
        pass
