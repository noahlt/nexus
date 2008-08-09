from django.db import models
from pdfutil import pdf_to_thumbnail, pdf_validator, joined_pdfs
from os.path import basename

class Page(models.Model):
    num = models.IntegerField()
    pdf = models.FileField(upload_to='pdf', validator_list=[pdf_validator])
    thumbnail = models.ImageField(editable=False, upload_to='thumbs')

    def __str__(self):
        return "%i : %s" % (self.num, basename(self.pdf))

    def save(self):
        self.thumbnail = pdf_to_thumbnail(self.pdf, 512)
        super(Page, self).save()

    class Meta:
        ordering = ['num']

    class Admin:
        pass

class Issue(models.Model):
    date = models.DateField()
    pages = models.ManyToManyField(Page)

    def get_thumbnail_url(self):
        return pdf_to_thumbnail(self.pages.all()[0].pdf, 256)

    def get_join_url(self):
        return joined_pdfs([page.pdf for page in self.pages.all()])

    def __str__(self):
        return "%s" % self.date

    class Meta:
        ordering = ['date']

    class Admin:
        pass
