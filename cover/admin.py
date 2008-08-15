from django.contrib import admin
from cover.models import *

admin.site.register(Author)
admin.site.register(Image, ImageAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
