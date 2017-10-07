# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# from modeltrans.fields import TranslationField


class Category(models.Model):
    name = models.CharField(max_length=255)

    # i18n = TranslationField(fields=('name', ), virtual_fields=False)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)

    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)

    # i18n = TranslationField(fields=('title', 'body'), virtual_fields=False)

    def __str__(self):
        return self.title
