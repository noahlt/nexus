from django.db import models
from pdfutil import pdf_to_thumbnail, pdf_validator, joined_pdfs, burst_pdf
from os.path import basename
from nexus import settings
from os import remove

STOCK_EMPTY_ISSUE = settings.MEDIA_ROOT + 'stock/EMPTY_ISSUE.pdf'

class SinglePage(models.Model):
    pdf = models.FileField(upload_to='/pdf')

    def __str__(self):
        return "%s" % basename(self.get_pdf_filename())

    def save(self):
        super(SinglePage, self).save()
        self.get_thumbnail_url() 

    def delete(self):
        try:
            remove(self.get_pdf_filename())
        except:
            pass
        super(SinglePage, self).delete()

    def get_thumbnail_url(self):
        return pdf_to_thumbnail(self.get_pdf_filename(), 512)

class PDF(models.Model):
    num = models.IntegerField()
    pdf = models.FileField(upload_to='pdf', validator_list=[pdf_validator])
    pages = models.ManyToManyField(SinglePage, editable=False, related_name='pages')

    def save(self):
        super(PDF, self).save()
        self.pages.clear()
        for page in burst_pdf(self.get_pdf_filename()):
            s = SinglePage(pdf=page)
            s.save()
            self.pages.add(s)
        self.get_thumbnail_url()

    def delete(self):
        for page in self.pages.all():
            page.delete()
        super(PDF, self).delete()

    def get_thumbnail_url(self):
        return pdf_to_thumbnail(self.get_pdf_filename(), 512)

    def __str__(self):
        return "%i : %s" % (self.num, basename(self.get_pdf_filename()))

    class Meta:
        ordering = ['num']

    class Admin:
        pass

class Issue(models.Model):
    date = models.DateField(unique=True)
    pages = models.ManyToManyField(PDF)

    def get_thumbnail_url(self):
        try:
            return pdf_to_thumbnail(self.pages.all()[0].get_pdf_filename(), 256)
        except IndexError: # someone deleted all the pages
            return pdf_to_thumbnail(STOCK_EMPTY_ISSUE, 256)

    def get_join_url(self):
        return joined_pdfs([page.get_pdf_filename() for page in self.pages.all()])

    def save(self):
        super(Issue, self).save()
        self.get_join_url()
        self.get_thumbnail_url()

    def __str__(self):
        return "%s" % self.date

    class Meta:
        ordering = ['-date']

    class Admin:
        pass
