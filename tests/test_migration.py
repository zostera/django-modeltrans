# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.utils.six import StringIO

from modeltrans.migration import I18nDataMigration, get_translatable_models

from .app.models import Blog, Category


def get_output(migration):
    output = StringIO()
    migration.write(output)
    return output.getvalue()


class I18nMigrationsTest(TestCase):
    def test_I18nDataMigration(self):
        m = I18nDataMigration("test_app")
        m.add_model(Blog, ("title_nl", "title_fr", "body_nl", "body_fr"))
        m.add_model(Category, ("name_nl", "name_fr"))

        output = get_output(m)
        self.assertTrue("Blog" in output)
        self.assertTrue("title_nl" in output)
        self.assertTrue("title_fr" in output)
        self.assertTrue("migrations.RunPython(forwards, migrations.RunPython.noop)" in output)

    def test_get_translatable_models(self):
        """
        get_translatable_models() Should only work if django-modeltranslation is
        available.
        So if this test fails in your dev environment, you probably have
        django-modeltranslation installed
        """

        with self.assertRaises(ImproperlyConfigured):
            get_translatable_models()
