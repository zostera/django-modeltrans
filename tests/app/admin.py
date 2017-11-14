# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from modeltrans.admin import ActiveLanguageMixin

from .models import Blog, Category, Site


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    pass


@admin.register(Site)
class SiteAdmin(ActiveLanguageMixin, admin.ModelAdmin):
    pass
