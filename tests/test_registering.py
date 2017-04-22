# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from modeltrans.exceptions import AlreadyRegistered
from modeltrans.translator import TranslationOptions, translator
from tests.app.models import Blog


class ReRegisterTest(TestCase):
    def test_re_register_model(self):
        class BlogTranslationOptions(TranslationOptions):
            fields = ('title', )

        with self.assertRaisesMessage(AlreadyRegistered, 'Model "Blog" is already registered for translation'):
            translator.register(Blog, BlogTranslationOptions)
