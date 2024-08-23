from django.contrib import admin

from modeltrans.admin import ActiveLanguageMixin, TabbedLanguageMixin

from .models import Blog, Category, Post, Site


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ("title_i18n", "category")
    search_fields = ("title_i18n", "category__name_i18n", "site__name")


@admin.register(Category)
class CategoryAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    pass


@admin.register(Site)
class SiteAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    pass


@admin.register(Post)
class PostAdmin(TabbedLanguageMixin, admin.ModelAdmin):
    pass
