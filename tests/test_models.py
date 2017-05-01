# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import override

from tests.app.models import Blog


class TranslatedFieldTest(TestCase):
    def test_get_active_language(self):
        m = Blog(title='Falcon', i18n={
            'title_nl': 'Valk',
            'title_de': 'Falk'
        })

        with override('nl'):
            # value for the active language
            self.assertEquals(m.title_i18n, 'Valk')

            self.assertEquals(m.title_en, 'Falcon')
            self.assertEquals(m.title_de, 'Falk')

        with override('de'):
            self.assertEquals(m.title_i18n, 'Falk')

    def test_get_has_no_translation(self):
        m = Blog(title='Falcon', i18n={
            'title_nl': 'Valk',
            'title_de': 'Falk'
        })

        # Fallback to base langauge
        with override('fr'):
            self.assertEquals(m.title_i18n, 'Falcon')

        # other translations are still there.
        self.assertEquals(m.title_nl, 'Valk')
        self.assertEquals(m.title_de, 'Falk')

    def test_get_non_translatable_field(self):
        m = Blog(title='Falcon')

        with self.assertRaisesMessage(AttributeError, "'Blog' object has no attribute 'foo'"):
            m.foo

    def test_set_translatable_field(self):
        m = Blog.objects.create(title='Toad')

        m.title_nl = 'Pad'
        m.save()

        self.assertEquals(Blog.objects.get(title='Toad').title_nl, 'Pad')

    def test_set_translatable_field_active_language(self):
        m = Blog.objects.create(title='Toad')

        with override('nl'):
            m.title_i18n = 'Pad'
        m.save()

        self.assertEquals(Blog.objects.get(title='Toad').title_nl, 'Pad')

    def test_set_default_langauge(self):
        m = Blog.objects.create(title='Toad 123')

        m.title_en = 'Toad'
        m.save()

        self.assertEquals(m.title, 'Toad')

    def test_clean(self):
        m = Blog(title='Horse', body='Horses are nice')

        with self.assertRaises(ValidationError) as e:
            m.full_clean()

        self.assertEquals(list(e.exception), [
            ('title_nl', ['This field cannot be null.'])
        ])

        # With an added `title_nl`, it should validate.
        m.title_nl = 'Paard'
        m.full_clean()


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
