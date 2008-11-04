from django.db import models
from django.contrib import admin

FILE_PATH = 'attach/'

class Attachment(models.Model):
    file = models.FileField(upload_to=FILE_PATH)
    parent = models.ForeignKey('Item')

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1

class Item(models.Model):
    subject = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=200, blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return "%s" % self.subject

    class Meta:
        ordering = ['-priority']

class ItemAdmin(admin.ModelAdmin):
    list_display = ('subject', 'status', 'priority')
    inlines = [AttachmentInline]
