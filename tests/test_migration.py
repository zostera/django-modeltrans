# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.utils.six import StringIO

from modeltrans.migration import I18nMigration, get_translatable_models

from .app.models import Blog, Category


class I18nMigrationTest(TestCase):
    def test_I18nMigration(self):
        m = I18nMigration('test_app')
        m.add_model(Blog, ('title_nl', 'title_fr', 'body_nl', 'body_fr'))
        m.add_model(Category, ('name_nl', 'name_fr'))

        output = StringIO()
        m.write(output)
        output = output.getvalue()

        self.assertTrue('Blog' in output)
        self.assertTrue('app_category_i18n_gin' in output)

    def test_get_translatable_models(self):
        '''
        get_translatable_models() Should only work if django-modeltranslation is
        available.
        So if this test fails in your dev environment, you probably have
        django-modeltranslation installed
        '''

        with self.assertRaises(ImproperlyConfigured):
            get_translatable_models()
