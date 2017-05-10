# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import SimpleTestCase

from modeltrans.migration import I18nMigration


class I18nMigrationTest(SimpleTestCase):
    def test_I18nMigration(self):
        m = I18nMigration('test_app')
        m.add_model('Blog', ('title_nl', 'title_fr', 'body_nl', 'body_fr'))
        m.add_model('Category', ('name_nl', 'name_fr'))
        m.write()
