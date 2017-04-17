# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import FieldError
from django.test import TestCase

from .models import Blog, BlogI18n


def key(queryset, key):
    return list([getattr(model, key) for model in queryset])


class FilterTest(TestCase):
    data = (
        ('Falcon', 'Valk'),
        ('Frog', 'Kikker'),
        ('Toad', 'Pad'),
        ('Duck', 'Eend'),
        ('Dolphin', 'Dolfijn')
    )

    def setUp(self):
        for title, title_nl in self.data:
            BlogI18n.objects.create(title=title, i18n={'title_nl': title_nl})

    def test_has_language(self):
        '''Check if a certain field is translated in a certain language'''

    def test_filter_contains(self):
        '''
        We want to do a text contains in translated value lookup
        '''
        qs = BlogI18n.objects.filter(title_nl__contains='al')
        self.assertEquals(qs[0].title_nl, 'Valk')

        qs = BlogI18n.objects.filter(title__contains='al')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_filter_exact(self):
        qs = BlogI18n.objects.filter(title_nl='Valk')
        self.assertEquals(qs[0].title, 'Falcon')

        qs = BlogI18n.objects.filter(title='Falcon')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_filter_startswith(self):
        qs = BlogI18n.objects.filter(title_nl__startswith='Va')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_exclude_exact(self):
        expected = {'Frog', 'Toad', 'Duck', 'Dolphin'}

        qs = BlogI18n.objects.exclude(title='Falcon')
        self.assertEquals({m.title for m in qs}, expected)

        qs = BlogI18n.objects.exclude(title_nl='Valk')
        self.assertEquals({m.title for m in qs}, expected)

        qs = BlogI18n.objects.exclude(title_nl='Valk').exclude(title_nl='Pad')
        self.assertEquals({m.title for m in qs}, {'Frog', 'Duck', 'Dolphin'})


class OrderByTest(TestCase):
    EN = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    NL = ['A', 'B', 'C', 'D', 'Z', 'Y', 'X']
    FR = ['1', '1', '1', '1', '2', '2', '2']

    def setUp(self):
        for i, en in enumerate(self.EN):
            BlogI18n.objects.create(title=en, i18n={'title_nl': self.NL[i], 'title_fr': self.FR[i]})

    def test_order_by_fails_for_normal_model(self):
        with self.assertRaises(FieldError):
            list(Blog.objects.all().order_by('title_nl'))

    def test_order_by_two_fields(self):
        '''Multiple translated fields should work too'''
        qs = BlogI18n.objects.all().order_by('-title_fr', 'title_nl')

        self.assertEquals(key(qs, 'title_nl'), 'X,Y,Z,A,B,C,D'.split(','))

    def test_order_asc(self):
        qs = BlogI18n.objects.all().order_by('title_nl')

        self.assertEquals(key(qs, 'title_nl'), sorted(self.NL))
        self.assertEquals(key(qs, 'title'), 'A,B,C,D,G,F,E'.split(','))

    def test_order_desc(self):
        qs = BlogI18n.objects.all().order_by('-title_nl')
        self.assertEquals(key(qs, 'title_nl'), sorted(self.NL, reverse=True))

        qs = BlogI18n.objects.all().order_by('-title')
        self.assertEquals(key(qs, 'title'), sorted(self.EN, reverse=True))
