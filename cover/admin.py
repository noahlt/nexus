from django.contrib import admin
from cover.models import *

admin.site.register(Title, TitleAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(InfoPage, InfoPageAdmin)
admin.site.register(CustomArticleTemplate, CustomArticleTemplateAdmin)
admin.site.register(SideBarLink, SideBarLinkAdmin)
