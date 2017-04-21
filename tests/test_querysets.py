# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import skip

from django.test import TestCase
from django.utils.translation import override

from tests.app.models import Blog, Site


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
            Blog.objects.create(title=title, i18n={'title_nl': title_nl})

    def test_has_language(self):
        '''Check if a certain field is translated in a certain language'''

    def test_filter_contains(self):
        '''
        We want to do a text contains in translated value lookup
        '''
        qs = Blog.objects.filter(title_nl__contains='al')
        self.assertEquals(qs[0].title_nl, 'Valk')

        qs = Blog.objects.filter(title__contains='al')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_filter_exact(self):
        qs = Blog.objects.filter(title_nl='Valk')
        self.assertEquals(qs[0].title, 'Falcon')

        qs = Blog.objects.filter(title='Falcon')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_filter_startswith(self):
        qs = Blog.objects.filter(title_nl__startswith='Va')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_exclude_exact(self):
        expected = {'Frog', 'Toad', 'Duck', 'Dolphin'}

        qs = Blog.objects.exclude(title='Falcon')
        self.assertEquals({m.title for m in qs}, expected)

        qs = Blog.objects.exclude(title_nl='Valk')
        self.assertEquals({m.title for m in qs}, expected)

        qs = Blog.objects.exclude(title_nl='Valk').exclude(title_nl='Pad')
        self.assertEquals({m.title for m in qs}, {'Frog', 'Duck', 'Dolphin'})

    def test_exclude_contains(self):
        qs = Blog.objects.exclude(title_nl__contains='o')
        self.assertEquals({m.title for m in qs}, {'Falcon', 'Frog', 'Toad', 'Duck'})

    def test_get(self):
        '''get() is just a special case of filter()'''
        b = Blog.objects.get(title_nl='Valk')

        self.assertEquals(b.title, 'Falcon')

        with self.assertRaisesMessage(Blog.DoesNotExist, 'Blog matching query does not exist.'):
            Blog.objects.get(title_fr='Boo')

    @skip('Not yet implemented')
    def test_filter_spanning_relation(self):
        '''
        Not sure if we should support this, but it requires having
        `MultilingualManager` on non-translated models too.
        '''
        Site.objects.filter(blog__title_nl__contains='al')


class OrderByTest(TestCase):
    EN = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    NL = ['A', 'B', 'C', 'D', 'Z', 'Y', 'X']
    FR = ['1', '1', '1', '1', '2', '2', '2']

    def setUp(self):
        for i, en in enumerate(self.EN):
            Blog.objects.create(title=en, i18n={'title_nl': self.NL[i], 'title_fr': self.FR[i]})

    def test_order_by_two_fields(self):
        '''Multiple translated fields should work too'''
        qs = Blog.objects.all().order_by('-title_fr', 'title_nl')

        self.assertEquals(key(qs, 'title_nl'), 'X,Y,Z,A,B,C,D'.split(','))

    def test_order_asc(self):
        qs = Blog.objects.all().order_by('title_nl')

        self.assertEquals(key(qs, 'title_nl'), sorted(self.NL))
        self.assertEquals(key(qs, 'title'), 'A,B,C,D,G,F,E'.split(','))

    def test_order_desc(self):
        qs = Blog.objects.all().order_by('-title_nl')
        self.assertEquals(key(qs, 'title_nl'), sorted(self.NL, reverse=True))

        qs = Blog.objects.all().order_by('-title')
        self.assertEquals(key(qs, 'title'), sorted(self.EN, reverse=True))


class TranslatedFieldGetTest(TestCase):
    def test_active_languate(self):
        m = Blog(title='Falcon', i18n={
            'title_nl': 'Valk',
            'title_de': 'Falk'
        })

        with override('nl'):
            self.assertEquals(m.title_en, 'Falcon')
            self.assertEquals(m.title_de, 'Falk')
            self.assertEquals(m.title_i18n, 'Valk')

        with override('de'):
            self.assertEquals(m.title_i18n, 'Falk')

    def test_has_no_translation(self):
        m = Blog(title='Falcon', i18n={
            'title_nl': 'Valk',
            'title_de': 'Falk'
        })

        with self.assertRaisesMessage(AttributeError, "'Blog.title' has no translation 'fr'"):
            m.title_fr

        self.assertEquals(m.title_nl, 'Valk')
        self.assertEquals(m.title_de, 'Falk')


class RefreshFromDbTest(TestCase):
    def test_refresh_from_db(self):
        b = Blog.objects.create(title='Falcon', i18n={
            'title_nl': 'Valk',
            'title_de': 'Falk'
        })

        Blog.objects.filter(title='Falcon').update(title='Falcon II')

        b.refresh_from_db()
        self.assertEquals(b.title, 'Falcon II')
        self.assertEquals(b.title_nl, 'Valk')


class CreatingInstancesTest(TestCase):
    def test_manager_create(self):
        b = Blog.objects.create(title='Falcon', title_nl='Valk')

        self.assertEquals(b.title, 'Falcon')
        self.assertEquals(b.title_nl, 'Valk')

    def test_manager_create_override(self):
        b = Blog.objects.create(title='Falcon', title_nl='Valk', i18n={
            'title_nl': 'foo'
        })

        self.assertEquals(b.title_nl, 'Valk')

    def test_model_constructor(self):
        b = Blog(title='Falcon', title_nl='Valk')
        b.save()

        self.assertEquals(b.title, 'Falcon')
        self.assertEquals(b.title_nl, 'Valk')
