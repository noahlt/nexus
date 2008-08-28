from django import forms
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from os.path import basename
from pdfutil import pdf_to_thumbnail, burst_pdf, validate_pdf, joined_pdfs

PDF_PATH = 'pdf_orig/'

class Page(models.Model):
    pdf = models.FileField(upload_to=PDF_PATH)
    parent = models.ForeignKey('PDF')

    def save(self):
        super(Page, self).save()
        self.calculate_thumbnail_url()

    def calculate_thumbnail_url(self):
        return pdf_to_thumbnail(self.pdf.path, 600)

    def __str__(self):
        try:
            return "%s" % basename(self.pdf.path)
        except ValueError:
            return "[corrupted file]"

    class Meta:
        ordering = ['pdf']

class PDF(models.Model):
    order = models.IntegerField(default=0)
    pdf = models.FileField(upload_to=PDF_PATH)
    parent = models.ForeignKey('Issue')

    def save(self):
        super(PDF, self).save()
        for page in self.page_set.all():
            page.delete()
        for page in burst_pdf(self.pdf.path):
            s = Page(pdf=page, parent=self)
            s.save()
            self.page_set.add(s)

    def __str__(self):
        try:
            return "%s" % basename(self.pdf.path)
        except ValueError:
            return "[corrupted file]"

    class Meta:
        ordering = ['order']

class PDFAdminForm(forms.ModelForm):
    def clean_pdf(self):
        validate_pdf(self.cleaned_data['pdf'])
        return self.cleaned_data['pdf']

class PDFInline(admin.TabularInline):
    model = PDF
    form = PDFAdminForm

class IssueAdminForm(forms.ModelForm):
    # XXX manual validation find why unique=True doesn't work
    # this case may be complicated by the inlined field
    def clean_date(self):
        if 'date' not in self.changed_data:
            return self.cleaned_data['date']
        try:
            Issue.objects.get(date=self.cleaned_data['date'])
        except ObjectDoesNotExist:
            return self.cleaned_data['date']
        raise forms.ValidationError("That date is already taken.")

class IssueAdmin(admin.ModelAdmin):
    inlines = [PDFInline]
    form = IssueAdminForm

class Issue(models.Model):
    date = models.DateField(unique=True)

    def calculate_thumbnail_url(self):
        try:
            the_actual_pdf = self.pdf_set.all()[0]
            the_page = the_actual_pdf.page_set.all()[0]
            return pdf_to_thumbnail(the_page.pdf.path, 320)
        except IndexError: # someone deleted all the pages
            return None

    def calculate_join_url(self):
        return joined_pdfs(self.pdf_set.all())

    def __str__(self):
        return "%s" % self.date

    class Meta:
        ordering = ['date']
