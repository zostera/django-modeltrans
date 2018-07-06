# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from modeltrans.manager import transform_translatable_fields
from modeltrans.utils import build_localized_fieldname, split_translated_fieldname
from tests.app.models import Blog


class UtilsTest(TestCase):
    def test_split_translated_fieldname(self):

        self.assertEqual(split_translated_fieldname("title_nl"), ("title", "nl"))

        self.assertEqual(split_translated_fieldname("full_name_nl"), ("full_name", "nl"))

    def test_transform_translatable_fields(self):
        self.assertEqual(
            transform_translatable_fields(Blog, {"title": "bar", "title_nl": "foo"}),
            {"i18n": {"title_nl": "foo"}, "title": "bar"},
        )

    def test_build_localized_fieldname(self):
        self.assertEqual(build_localized_fieldname("title", "nl"), "title_nl")
        self.assertEqual(build_localized_fieldname("category__name", "nl"), "category__name_nl")
