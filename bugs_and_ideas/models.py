from django.db import models
from django.contrib import admin

class Item(models.Model):
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=200, blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return "%s" % self.subject

    class Meta:
        ordering = ['-priority']

class ItemAdmin(admin.ModelAdmin):
    list_display = ('subject', 'status', 'priority')
