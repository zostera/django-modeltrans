# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from modeltrans.admin import ActiveLanguageMixin

from .models import Blog, Category
from .utils import disable_admin_login

admin.site.has_permission = disable_admin_login()


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    pass



class DefaultAdminCategory(Category):
    '''
    Proxy model to have both the unlimited version of the ModelAdmin and
    a limited version
    '''
    class Meta:
        proxy = True


@admin.register(DefaultAdminCategory)
class DefaultCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    pass
