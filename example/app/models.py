# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from modeltrans.fields import TranslationField


@python_2_unicode_compatible
class Category(models.Model):
    name = models.CharField(max_length=255)

    i18n = TranslationField(fields=('name', ))

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name_i18n


@python_2_unicode_compatible
class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)

    category = models.ForeignKey(Category, null=True, blank=True)

    i18n = TranslationField(fields=('title', 'body', ))

    def __str__(self):
        return self.title_i18n
