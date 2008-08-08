from django.db import models

class Page(models.Model):
    pdf = models.FileField(upload_to='pdf')
    num = models.IntegerField()
    thumbnail = models.ImageField(upload_to='thumbs', blank=True, null=True)

    def __str__(self):
        return "%s" % self.pdf

    class Meta:
        ordering = ["num"]

class Issue(models.Model):
    date = models.DateField()
    pages = models.ManyToManyField(Page)
    thumbnail = models.ImageField(upload_to='thumbs', blank=True, null=True)

    def __str__(self):
        return "%s" % self.date

    class Meta:
        ordering = ["date"]
