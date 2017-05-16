# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.test import TestCase

from modeltrans.decorators import register
from modeltrans.exceptions import AlreadyRegistered
from modeltrans.manager import MultilingualManager, MultilingualQuerySet, get_translatable_fields_for_model
from modeltrans.translator import TranslationOptions, translator
from tests.app.models import Blog


class ReRegisterTest(TestCase):
    def test_re_register_model(self):
        class BlogTranslationOptions(TranslationOptions):
            fields = ('title', )

        with self.assertRaisesMessage(AlreadyRegistered, 'Model "Blog" is already registered for translation'):
            translator.register(Blog, BlogTranslationOptions)

    def test_register_with_invalid_language(self):
        class TestModel(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )
            required_languages = ('en', 'nl', 'spanisch')

        expected_message = (
            'Language "spanisch" is in required_languages on '
            'Model "TestModel" but not in settings.AVAILABLE_LANGUAGES.'
        )

        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translator.register(TestModel, TestModelTranslationOptions)

    def test_register_with_invalid_language_dict(self):
        class TestModel2(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )
            required_languages = {
                'vlaams': ('name', )
            }
        expected_message = (
            'Language "vlaams" is in required_languages on Model "TestModel2" '
            'but not in settings.AVAILABLE_LANGUAGES.'
        )
        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translator.register(TestModel2, TestModelTranslationOptions)

    def test_register_with_invalid_field(self):
        class TestModel3(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )
            required_languages = {
                'en': ('title', )
            }
        expected_message = (
            'Fieldname "title" in required_languages which is not defined as '
            'translatable for Model "TestModel3".'
        )
        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translator.register(TestModel3, TestModelTranslationOptions)

    def test_register_model_with_custom_manager(self):

        class CustomQuerySet(models.query.QuerySet):
            pass

        class CustomManager(models.Manager):
            def get_queryset(self):
                return CustomQuerySet()

            def custom_method(self):
                return 'foo'

        class TestModel4(models.Model):
            name = models.CharField(max_length=100)

            objects = CustomManager()

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )

        translator.register(TestModel4, TestModelTranslationOptions)

        self.assertIsInstance(TestModel4.objects, CustomManager)
        self.assertIsInstance(TestModel4.objects, MultilingualManager)

        self.assertEquals(TestModel4.objects.custom_method(), 'foo')
        self.assertIsInstance(TestModel4.objects.all(), MultilingualQuerySet)

    def test_get_translatable_fiels_for_model(self):
        class TestModel5(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        fields = get_translatable_fields_for_model(TestModel5)
        self.assertEquals(fields, None)

    def test_unintended_string_to_tuple(self):
        class TestModel6(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name')   # note the missing comma

        # due to different hash algorithms, any char of the field name can occur
        # in the message
        expected_message = (
            r'Attribute TestModel6TranslationOptions\.fields contains an item "[name]", '
            'which is not a field \(missing a comma\?\)\.'
        )

        with self.assertRaisesRegexp(ImproperlyConfigured, expected_message):
            translator.register(TestModel6, TestModelTranslationOptions)

    def test_use_decorator(self):
        class TestModel7(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        @register(TestModel7)
        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )

        # TODO: verify the model is registered indeed.

    def test_decorator_incorrect_options_object(self):
        class TestModel8(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        with self.assertRaisesMessage(ValueError, 'Wrapped class must subclass TranslationOptions.'):
            @register(TestModel8)
            class TestModelTranslationOptions(object):
                fields = ('name', )

    def test_register_without_virtual_fields(self):
        translator.set_create_virtual_fields(False)

        class TestModel9(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        @register(TestModel9)
        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )

        m = TestModel9(name='foo')
        self.assertTrue(hasattr(m, 'i18n'))
        self.assertFalse(hasattr(m, 'name_i18n'))
        self.assertFalse(hasattr(m, 'name_en'))

        with self.assertRaisesMessage(TypeError, "'name_nl' is an invalid keyword argument for this function"):
            TestModel9(name='bar', name_nl='foo')

        translator.set_create_virtual_fields(True)

    def test_field_gets_original_validators(self):
        def validator(value):
            if value in (None, ''):
                return

            if int(value) < 20:
                raise ValidationError('must be equal to or greater than 20.')

        class TestModel10(models.Model):
            name = models.CharField(max_length=100, validators=[validator, ])

            class Meta:
                app_label = 'django-modeltrans_tests'

        @register(TestModel10)
        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )

        field = TestModel10._meta.get_field('name')
        self.assertTrue(validator in field.validators)

        field = TestModel10._meta.get_field('name_nl')
        self.assertTrue(validator in field.validators)

        m = TestModel10(name='22', name_nl='10')
        with self.assertRaises(ValidationError) as e:
            m.full_clean()

        self.assertEquals(list(e.exception), [
            ('name_nl', ['must be equal to or greater than 20.']),
        ])
