# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import FieldError
from django.test import TestCase

from .models import Blog, BlogI18n


def key(queryset, key):
    return list([getattr(model, key) for model in queryset])


class OrderByTest(TestCase):
    EN = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    NL = ['A', 'B', 'C', 'D', 'Z', 'Y', 'X']

    def setUp(self):
        for i, en in enumerate(self.EN):
            BlogI18n.objects.create(title=en, i18n={'title_nl': self.NL[i]})

    def test_order_by_fails_for_normal_model(self):

        with self.assertRaises(FieldError):
            list(Blog.objects.all().order_by('title_nl'))

    def test_order_asc(self):
        qs = BlogI18n.objects.all().order_by('title_nl')

        self.assertEquals(key(qs, 'title_nl'), sorted(self.NL))
        self.assertEquals(key(qs, 'title'), 'A,B,C,D,G,F,E'.split(','))

    def test_order_desc(self):
        qs = BlogI18n.objects.all().order_by('-title_nl')
        self.assertEquals(key(qs, 'title_nl'), sorted(self.NL, reverse=True))
