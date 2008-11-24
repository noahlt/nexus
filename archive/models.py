from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import models
from os.path import basename
from pdfutil import pdf_to_thumbnail, validate_pdf, joined_pdfs
from datetime import date

PDF_PATH = 'pdf_orig/'
FILE_PATH = 'upload/'

def ignore_errors(f):
    def _f(*args):
        try:
            return f(*args)
        except:
            return None
    return _f

class File(models.Model):
    file = models.FileField(upload_to=FILE_PATH)

    def __str__(self):
        return "%s%s" % (settings.MEDIA_URL, self.file)

class PDF(models.Model):
    order = models.IntegerField(default=0)
    pdf = models.FileField(upload_to=PDF_PATH)
    parent = models.ForeignKey('Issue')

    @ignore_errors
    def calculate_thumbnail_url(self):
        return pdf_to_thumbnail(self.pdf.path, 250)

    def save(self):
        super(PDF, self).save()
        self.calculate_thumbnail_url()

    @ignore_errors
    def __str__(self):
        return "%s" % basename(self.pdf.path)

    class Meta:
        ordering = ['order', 'id']

class PDFAdminForm(forms.ModelForm):
    def clean_pdf(self):
        validate_pdf(self.cleaned_data['pdf'])
        return self.cleaned_data['pdf']

class PDFInline(admin.TabularInline):
    model = PDF
    form = PDFAdminForm

class IssueAdmin(admin.ModelAdmin):
    inlines = [PDFInline]
    def visible(obj):
        return obj.current()
    visible.boolean = True
    list_display = ('date', visible)

class Issue(models.Model):
    date = models.DateField(unique=True, help_text="Issues from the future will not be shown.")

    @ignore_errors
    def calculate_thumbnail_url(self):
        the_actual_pdf = self.pdf_set.all()[0]
        return pdf_to_thumbnail(the_actual_pdf.pdf.path, 160)

    @ignore_errors
    def calculate_back_url(self):
        the_actual_pdf = self.pdf_set.all().reverse()[0]
        return pdf_to_thumbnail(the_actual_pdf.pdf.path, 120)

    def current(self):
        return self.date <= date.today()

    @ignore_errors
    def calculate_join_url(self):
        return joined_pdfs(self.pdf_set.all(), self.id)

    def __str__(self):
        return "%s" % self.date

    class Meta:
        ordering = ['-date', 'id']
