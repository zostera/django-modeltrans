# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.forms import ModelForm

from modeltrans.migration import I18nDataMigration, I18nIndexMigration, get_translatable_models

from .app.models import Blog, Category


# class ModelFormTest(TestCase):
#     def test_modelform(self):
#
#         class BlogForm(ModelForm):
#             class Meta:
#                 model = Blog
#                 fields = ('title_i18n', 'body_i18n', )
