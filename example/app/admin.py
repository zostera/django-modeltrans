from django.contrib import admin

from modeltrans.admin import ActiveLanguageMixin

from .models import Blog, Category
from .utils import disable_admin_login

admin.site.has_permission = disable_admin_login()


@admin.register(Blog)
class BlogAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    list_display = ("title_i18n", "category")
    search_fields = ("title_i18n", "category__name_i18n")


class DefaultAdminCategory(Category):
    """
    Proxy model to have both the unlimited version of the ModelAdmin and a limited version with all
    fields but the default language and the current language excluded.
    """

    class Meta:
        proxy = True


@admin.register(DefaultAdminCategory)
class DefaultCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    pass
