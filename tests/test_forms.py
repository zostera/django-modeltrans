# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import FieldError
from django.forms import modelform_factory
from django.test import TestCase

from .app.models import Blog


class ModelFormTest(TestCase):
    def test_i18n_virt_field_modelform(self):
        with self.assertRaises(FieldError) as err:
            modelform_factory(Blog, fields=("title_i18n",))
        self.assertIn("'title_i18n' cannot be specified for Blog", str(err.exception))
