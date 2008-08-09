from django.db import models
from pdfutil import pdf_to_thumbnail, pdf_validator, joined_pdfs
from os.path import basename
from nexus import settings

STOCK_EMPTY_ISSUE = settings.MEDIA_ROOT + 'stock/EMPTY_ISSUE.pdf'

class Page(models.Model):
    num = models.IntegerField()
    pdf = models.FileField(upload_to='pdf', validator_list=[pdf_validator])

    def __str__(self):
        return "%i : %s" % (self.num, basename(self.get_pdf_filename()))

    def get_thumbnail_url(self):
        return pdf_to_thumbnail(self.get_pdf_filename(), 512)

    class Meta:
        ordering = ['num']

    class Admin:
        pass

class Issue(models.Model):
    date = models.DateField(unique=True)
    pages = models.ManyToManyField(Page)

    def get_thumbnail_url(self):
        try:
            return pdf_to_thumbnail(self.pages.all()[0].get_pdf_filename(), 256)
        except IndexError: # someone deleted all the pages
            return pdf_to_thumbnail(STOCK_EMPTY_ISSUE, 256)

    def get_join_url(self):
        return joined_pdfs([page.get_pdf_filename() for page in self.pages.all()])

    def __str__(self):
        return "%s" % self.date

    class Meta:
        ordering = ['-date']

    class Admin:
        pass
