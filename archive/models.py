from django import forms
from django.contrib import admin
from django.db import models
from nexus import settings
from os import remove
from os.path import basename
from pdfutil import *

STOCK_EMPTY_ISSUE = settings.MEDIA_ROOT + 'stock/EMPTY_ISSUE.pdf'

class SinglePage(models.Model):
    pdf = models.FileField(upload_to='/pdf')

    def __str__(self):
        return "%s" % basename(self.pdf.path)

    def save(self):
        super(SinglePage, self).save()
        self.calculate_thumbnail_url() 

    def delete(self):
        try:
            remove(self.pdf.path)
        except:
            pass
        super(SinglePage, self).delete()

    def calculate_thumbnail_url(self):
        return pdf_to_thumbnail(self.pdf.path, 512)

class PDF(models.Model):
    num = models.IntegerField()
    pdf = models.FileField(upload_to='pdf')
    pages = models.ManyToManyField(SinglePage, editable=False, related_name='pages')

    def save(self):
        super(PDF, self).save()
        self.pages.clear()
        for page in burst_pdf(self.pdf.path):
            s = SinglePage(pdf=page)
            s.save()
            self.pages.add(s)

    def delete(self):
        for page in self.pages.all():
            page.delete()
        super(PDF, self).delete()

    def calculate_thumbnail_url(self):
        return self.pages.all()[0].calculate_thumbnail_url()

    def __str__(self):
        return "%i : %s" % (self.num, basename(self.pdf.path))

    class Meta:
        ordering = ['num']

class PDFAdminForm(forms.ModelForm):
    def clean_pdf(self):
        validate_pdf(self.cleaned_data['pdf'])
        return self.cleaned_data['pdf']

class PDFAdmin(admin.ModelAdmin):
    form = PDFAdminForm

class Issue(models.Model):
    date = models.DateField(unique=True)
    pages = models.ManyToManyField(PDF)

    def calculate_thumbnail_url(self):
        try:
            return pdf_to_thumbnail(self.pages.all()[0].pdf.path, 256)
        except IndexError: # someone deleted all the pages
            return pdf_to_thumbnail(STOCK_EMPTY_ISSUE, 256)

    def calculate_join_url(self):
        return joined_pdfs([page.pdf.path for page in self.pages.all()])

    def save(self):
        super(Issue, self).save()
        self.calculate_join_url()
        self.calculate_thumbnail_url()

    def __str__(self):
        return "%s" % self.date

    class Meta:
        ordering = ['-date']
