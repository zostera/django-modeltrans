# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import DataError, transaction
from django.test import TestCase, override_settings
from django.utils.translation import override

from tests.app.models import Blog, NullableTextModel, TextModel


class TranslatedFieldTest(TestCase):
    def test_get_active_language(self):
        m = Blog(title="Falcon", i18n={"title_nl": "Valk", "title_de": "Falk"})

        with override("nl"):
            # value for the active language
            self.assertEqual(m.title_i18n, "Valk")

            self.assertEqual(m.title_en, "Falcon")
            self.assertEqual(m.title_de, "Falk")

        with override("de"):
            self.assertEqual(m.title_i18n, "Falk")

    def test_get_has_no_translation(self):
        m = Blog(title="Falcon", i18n={"title_nl": "Valk", "title_de": "Falk"})

        # Fallback to base langauge
        with override("fr"):
            self.assertEqual(m.title_i18n, "Falcon")

        # other translations are still there.
        self.assertEqual(m.title_nl, "Valk")
        self.assertEqual(m.title_de, "Falk")

    def test_get_non_translatable_field(self):
        m = Blog(title="Falcon")

        with self.assertRaisesMessage(AttributeError, "'Blog' object has no attribute 'foo'"):
            m.foo

    def test_set_translatable_field(self):
        m = Blog.objects.create(title="Toad")

        m.title_nl = "Pad"
        m.save()

        self.assertEqual(Blog.objects.get(title="Toad").title_nl, "Pad")

    def test_set_translatable_field_active_language(self):
        m = Blog.objects.create(title="Toad")

        with override("nl"):
            m.title_i18n = "Pad"
        m.save()

        self.assertEqual(Blog.objects.get(title="Toad").title_nl, "Pad")

    def test_set_default_langauge(self):
        m = Blog.objects.create(title="Toad 123")

        m.title_en = "Toad"
        m.save()

        self.assertEqual(m.title, "Toad")

    def test_set_None_doesnt_result_in_null_keys(self):
        m = Blog.objects.create(title="Couch")
        m.title_nl = None
        m.save()

        m = Blog.objects.get(title="Couch")
        self.assertEqual(m.i18n, {})

        m.title_nl = "Bank"
        m.save()
        self.assertEqual(m.i18n, {"title_nl": "Bank"})

        m.title_nl = None
        m.save()
        self.assertEqual(m.i18n, {})

    def test_fallback_getting_CharField(self):
        m = Blog.objects.create(title="Falcon")
        with override("de"):
            self.assertEqual(m.title_i18n, "Falcon")

        # this empty string in title_fr might be the result of an admin edit
        m = Blog.objects.create(title="Falcon", title_fr="")
        with override("fr"):
            self.assertEqual(m.title_i18n, "Falcon")

        # should also fallback if a value is None
        m = Blog.objects.create(title="Falcon", title_fr=None)
        with override("fr"):
            self.assertEqual(m.title_i18n, "Falcon")

        # should not fallback with string 'False'
        m = Blog.objects.create(title="Falcon", title_fr="False")
        with override("fr"):
            self.assertEqual(m.title_i18n, "False")

    def test_fallback_getting_TextField(self):
        DESCRIPTION = "Story about Falcon"
        m = TextModel(title="Falcon", description_en=DESCRIPTION)
        with override("fr"):
            self.assertEqual(m.description_i18n, DESCRIPTION)

        m = NullableTextModel.objects.create(description=DESCRIPTION, description_fr="")
        with override("fr"):
            self.assertEqual(m.description_i18n, DESCRIPTION)

    def test_creating_using_virtual_default_language_field(self):
        m = Blog.objects.create(title_en="Falcon")

        self.assertEqual(m.title, "Falcon")

    def test_creationg_prevents_double_definition(self):
        expected_message = (
            'Attempted override of "title" with "title_en". Only ' "one of the two is allowed."
        )
        with self.assertRaisesMessage(ValueError, expected_message):
            Blog.objects.create(title="Foo", title_en="Bar")

    def test_creating_with_nonexisting_field(self):
        """
        Blogs have titles, not names, so trying to add something with a name
        should raise an eror.
        """
        expected_message = "'name' is an invalid keyword argument for this function"

        with self.assertRaisesMessage(TypeError, expected_message):
            Blog.objects.create(name="Falcon")

        expected_message = "'name_nl' is an invalid keyword argument for this function"
        with self.assertRaisesMessage(TypeError, expected_message):
            Blog.objects.create(title="Falcon", name_nl="Valk")

    def test_clean(self):
        """
        Blog has required_languages=('nl', ), so this should raise an error
        if `title_nl` is not set.
        """
        m = Blog(title="Horse", body="Horses are nice")

        with self.assertRaises(ValidationError) as e:
            m.full_clean()

        self.assertEqual(
            {(field, tuple(errors)) for field, errors in e.exception},
            {
                ("title_nl", ("This field cannot be null.",)),
                ("body_nl", ("This field cannot be null.",)),
            },
        )

        # With an added `title_nl`, it should validate.
        m.title_nl = "Paard"
        m.body_nl = "foo"
        m.full_clean()

    def test_textfield(self):
        """
        Constrains on the original field should also be enforced on the
        translated virtual fields (except for null/blank).

        Note that the database contraints are not enforced on the virtual fields,
        because those are ignored by Django.
        """

        expected_message = "value too long for type character varying(50)"

        short_str = "bla bla"
        long_str = "bla" * 40

        with transaction.atomic():
            with self.assertRaisesMessage(DataError, expected_message):
                TextModel.objects.create(title=long_str)

        with self.assertRaises(ValidationError) as e:
            b = TextModel.objects.create(title=short_str, title_nl=long_str)
            b.full_clean()

        self.assertEqual(
            sorted(list(e.exception), key=lambda v: v[0]),
            [
                ("description", ["This field cannot be blank."]),
                ("title_nl", ["Ensure this value has at most 50 characters (it has 120)."]),
            ],
        )

        TextModel.objects.create(title=short_str, description=long_str)

        m = TextModel.objects.create(
            title=short_str, description=short_str, description_nl=long_str, description_de=long_str
        )
        self.assertEqual(m.description_nl, long_str)

    @override_settings(
        MODELTRANS_AVAILABLE_LANGUAGES=("fr", "fy", "nl"),
        MODELTRANS_FALLBACK={"default": ("en",), "fy": ("nl", "en")},
    )
    def test_fallback_chain(self):
        """
        Testing the fallback chain setting for model
        """
        b = Blog.objects.create(
            title="Buzzard",
            i18n={"title_fy": "Mûzefalk", "title_nl": "Buizerd", "title_fr": "Buse"},
        )

        with override("nl"):
            self.assertEqual(b.title_i18n, "Buizerd")
        with override("fr"):
            self.assertEqual(b.title_i18n, "Buse")
        with override("fy"):
            self.assertEqual(b.title_i18n, "Mûzefalk")

        b = Blog.objects.create(title="Buzzard", i18n={"title_nl": "Buizerd", "title_fr": "Buse"})
        with override("fy"):
            self.assertEqual(b.title_i18n, "Buizerd")

        b = Blog.objects.create(title="Buzzard", i18n={"title_fr": "Buse"})
        with override("fy"):
            self.assertEqual(b.title_i18n, "Buzzard")
        with override("fr"):
            self.assertEqual(b.title_i18n, "Buse")

    def test_defer_i18n(self):
        Blog.objects.create(title="Buzzard", title_nl="Buizerd")

        qs = Blog.objects.defer("i18n")

        blog = qs[0]
        self.assertEqual(blog.get_deferred_fields(), {"i18n"})

        with self.assertRaises(ValueError):
            blog.title_i18n


class RefreshFromDbTest(TestCase):
    def test_refresh_from_db(self):
        b = Blog.objects.create(title="Falcon", i18n={"title_nl": "Valk", "title_de": "Falk"})
        Blog.objects.filter(title="Falcon").update(title="Falcon II")

        b.refresh_from_db()
        self.assertEqual(b.title, "Falcon II")
        self.assertEqual(b.title_nl, "Valk")


class CreatingInstancesTest(TestCase):
    def test_manager_create(self):
        b = Blog.objects.create(title="Falcon", title_nl="Valk")

        self.assertEqual(b.title, "Falcon")
        self.assertEqual(b.title_nl, "Valk")

    def test_manager_create_override(self):
        b = Blog.objects.create(title="Falcon", title_nl="Valk", i18n={"title_nl": "foo"})

        self.assertEqual(b.title_nl, "Valk")

    def test_model_constructor(self):
        b = Blog(title="Falcon", title_nl="Valk")
        b.save()

        self.assertEqual(b.title, "Falcon")
        self.assertEqual(b.title_nl, "Valk")

    def test_get_or_create(self):
        kwargs = dict(title="Falcon", title_nl="Valk")

        a = Blog.objects.create(**kwargs)
        b, created = Blog.objects.get_or_create(**kwargs)
        self.assertFalse(created)

        self.assertEqual(a, b)
        c, created = Blog.objects.get_or_create(title="Falcon")
        self.assertEqual(c, a)

        kwargs = dict(title="Buzzard", title_nl="Buizerd")
        a, _ = Blog.objects.get_or_create(**kwargs)
        b, created = Blog.objects.get_or_create(**kwargs)
        self.assertEqual(a, b)

    def test_update_or_create(self):
        a = Blog.objects.create(title="Falcon")

        defaults = dict(title_nl="Valk", title_de="Falk")
        b, created = Blog.objects.update_or_create(defaults=defaults, title="Falcon")
        self.assertFalse(created)
        self.assertEqual(a, b)

        a.refresh_from_db()
        self.assertEqual(a.title_de, defaults["title_de"])
