# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.test import TestCase

from modeltrans.fields import TranslationField
from modeltrans.manager import MultilingualManager, MultilingualQuerySet
from modeltrans.translator import get_i18n_field, get_translated_models, translate_model

from .app import models as app_models


class Translating_utils(TestCase):
    def test_get_i18n_field(self):
        self.assertEqual(get_i18n_field(app_models.Blog), app_models.Blog._meta.get_field("i18n"))

        class I18nFieldTestModel(models.Model):
            test = models.CharField(max_length=20)

            class Meta:
                app_label = "django-modeltrans_tests"

        self.assertEqual(get_i18n_field(I18nFieldTestModel), None)

        class I18nFieldTestModel2(models.Model):
            test = models.CharField(max_length=20)
            i18n = models.CharField(max_length=20)

            class Meta:
                app_label = "django-modeltrans_tests"

        self.assertEqual(get_i18n_field(I18nFieldTestModel2), None)

    def test_get_translated_models(self):
        expected = {
            app_models.Blog,
            app_models.Category,
            app_models.Person,
            app_models.TextModel,
            app_models.NullableTextModel,
            app_models.Attribute,
            app_models.Choice,
        }
        self.assertEqual(set(get_translated_models("app")), expected)


class TranslateModelTest(TestCase):
    def test_translate_bad_required_language_type(self):
        class BadRequiredLanguagesType(models.Model):
            title = models.CharField(max_length=100)

            i18n = TranslationField(fields=("title",), required_languages=("es"))

            class Meta:
                app_label = "django-modeltrans_tests"

        expected_message = '"required_languages" must be a tuple, list or set'
        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translate_model(BadRequiredLanguagesType)

    def test_translate_bad_required_language(self):
        class A(models.Model):
            title = models.CharField(max_length=100)

            i18n = TranslationField(fields=("title",), required_languages=("es",))

            class Meta:
                app_label = "django-modeltrans_tests"

        expected_message = (
            'Language "es" is in required_languages on '
            'Model "A" but not in settings.MODELTRANS_AVAILABLE_LANGUAGES.'
        )
        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translate_model(A)

    def test_translation_unsupported_field(self):
        class IntegerModel(models.Model):
            integer = models.IntegerField()
            i18n = TranslationField(fields=("integer",))

            class Meta:
                app_label = "django-modeltrans_tests"

        expected_message = "IntegerField is not supported by django-modeltrans."

        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translate_model(IntegerModel)

    def test_translation_field_is_not_named_i18n(self):
        expected_message = 'TranslationField must have name "i18n"'

        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):

            class BadlyNamedTranslationField(models.Model):
                i19n = TranslationField(fields=())

                class Meta:
                    app_label = "django-modeltrans_tests"

    def test_translate_nonexisting_field(self):
        class B(models.Model):
            i18n = TranslationField(fields=("foo",))

            class Meta:
                app_label = "django-modeltrans_tests"

        expected_message = (
            'Argument "fields" to TranslationField contains an item "foo", '
            "which is not a field (missing a comma?)."
        )

        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translate_model(B)

    def test_translate_model_with_custom_manager(self):
        """
        Verify the MultiLingualManager gets mixed in properly
        """

        class CustomQuerySet(models.query.QuerySet):
            pass

        class CustomManager(models.Manager):
            def get_queryset(self):
                return CustomQuerySet()

            def custom_method(self):
                return "foo"

        class TestModel1(models.Model):
            name = models.CharField(max_length=100)

            i18n = TranslationField(fields=("name",))

            objects = CustomManager()

            class Meta:
                app_label = "django-modeltrans_tests"

        translate_model(TestModel1)

        self.assertIsInstance(TestModel1.objects, CustomManager)
        self.assertIsInstance(TestModel1.objects, MultilingualManager)

        self.assertEqual(TestModel1.objects.custom_method(), "foo")
        self.assertIsInstance(TestModel1.objects.all(), MultilingualQuerySet)

    def test_translate_model_with_existing_field(self):
        class TestModel2(models.Model):
            title = models.CharField(max_length=100)
            title_nl = models.CharField(max_length=100)

            i18n = TranslationField(fields=("title",))

            class Meta:
                app_label = "django-modeltrans_tests"

        expected_message = (
            'Error adding translation field. Model "TestModel2" already '
            'contains a field named "title_nl".'
        )

        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translate_model(TestModel2)

    def test_translate_model_with_non_modeltrans_i18n_field(self):
        class TestModel3(models.Model):
            title = models.CharField(max_length=100)
            i18n = models.BooleanField()

            class Meta:
                app_label = "django-modeltrans_tests"

        translate_model(TestModel3)

    def test_translate_without_virtual_fields(self):
        class TestModel4(models.Model):
            title = models.CharField(max_length=100)

            i18n = TranslationField(fields=("title",), virtual_fields=False)

            class Meta:
                app_label = "django-modeltrans_tests"

        m = TestModel4(title="foo")
        self.assertTrue(hasattr(m, "i18n"))
        self.assertFalse(hasattr(m, "title_i18n"))
        self.assertFalse(hasattr(m, "title_en"))

        expected_message = "'title_nl' is an invalid keyword argument for this function"

        with self.assertRaisesMessage(TypeError, expected_message):
            TestModel4(title="bar", title_nl="foo")

    def test_field_gets_original_validators(self):
        def validator(value):
            if value in (None, ""):
                return

            if int(value) < 20:
                raise ValidationError("must be equal to or greater than 20.")

        class TestModel5(models.Model):
            title = models.CharField(max_length=100, validators=[validator])

            i18n = TranslationField(fields=("title",))

            class Meta:
                app_label = "django-modeltrans_tests"

        translate_model(TestModel5)

        field = TestModel5._meta.get_field("title")
        self.assertTrue(validator in field.validators)

        field = TestModel5._meta.get_field("title_nl")
        self.assertTrue(validator in field.validators)

        m = TestModel5(title="22", title_nl="10")
        with self.assertRaises(ValidationError) as e:
            m.full_clean()

        self.assertEqual(
            list(e.exception), [("title_nl", ["must be equal to or greater than 20."])]
        )

    def test_model_meta_ordering_pk(self):
        """
        When Model.Meta.ordering contains 'pk'
        """

        class OrderByPkModel(models.Model):
            title = models.CharField(max_length=100)

            i18n = TranslationField(fields=("title",))

            class Meta:
                app_label = "django-modeltrans_tests"
                ordering = ("-pk",)

        translate_model(OrderByPkModel)
        sql = str(OrderByPkModel.objects.all().query)

        self.assertIn('ORDER BY "django-modeltrans_tests_orderbypkmodel"."id" DESC', sql)
