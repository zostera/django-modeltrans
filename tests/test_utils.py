# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from modeltrans.manager import split_translated_fieldname


class TranslatedFieldTest(TestCase):
    def test_split_translated_fieldname(self):

        self.assertEquals(
            split_translated_fieldname('title_nl'),
            ('title', 'nl')
        )

        self.assertEquals(
            split_translated_fieldname('full_name_nl'),
            ('full_name', 'nl')
        )
