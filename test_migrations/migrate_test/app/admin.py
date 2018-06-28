# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Blog, Category


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ("title", "category")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass
