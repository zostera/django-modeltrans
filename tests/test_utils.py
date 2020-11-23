from django.test import TestCase
from django.utils.translation import override

from modeltrans.manager import transform_translatable_fields
from modeltrans.utils import (
    build_localized_fieldname,
    get_instance_field_value,
    get_language,
    get_model_field,
    split_translated_fieldname,
)

from .app.models import Blog, Category


class UtilsTest(TestCase):
    def test_get_language(self):
        self.assertEqual(get_language(), "en")

        with override("nl"):
            self.assertEqual(get_language(), "nl")

        with override("id"):
            self.assertEqual(get_language(), "en")

    def test_split_translated_fieldname(self):
        self.assertEqual(split_translated_fieldname("title_nl"), ("title", "nl"))

        self.assertEqual(split_translated_fieldname("full_name_nl"), ("full_name", "nl"))

    def test_transform_translatable_fields(self):
        self.assertEqual(
            transform_translatable_fields(Blog, {"title": "bar", "title_nl": "foo"}),
            {"i18n": {"title_nl": "foo"}, "title": "bar"},
        )

    def test_transform_translatable_fields_without_translations(self):
        self.assertEqual(
            transform_translatable_fields(Blog, {"title": "bar", "title_nl": "foo", "i18n": None}),
            {"i18n": {"title_nl": "foo"}, "title": "bar"},
        )

    def test_transform_translatable_fields_keep_translations(self):
        self.assertEqual(
            transform_translatable_fields(
                Blog, {"title": "bar", "title_de": "das foo", "i18n": {"title_nl": "foo"}}
            ),
            {"i18n": {"title_nl": "foo", "title_de": "das foo"}, "title": "bar"},
        )

    def test_build_localized_fieldname(self):
        self.assertEqual(build_localized_fieldname("title", "nl"), "title_nl")
        self.assertEqual(build_localized_fieldname("category__name", "nl"), "category__name_nl")
        self.assertEqual(build_localized_fieldname("title", "id"), "title_ind")
        self.assertEqual(build_localized_fieldname("title", "en-US"), "title_en_US")

    def test_get_model_field(self):
        with self.assertRaises(ValueError):
            get_model_field(object(), "name")
        self.assertEqual(get_model_field(Category, "name"), Category._meta.get_field("name"))
        self.assertEqual(get_model_field(Category, "color"), None)
        self.assertEqual(get_model_field(Blog, "category__name"), Category._meta.get_field("name"))
        self.assertEqual(get_model_field(Blog, "category__color"), None)

    def test_get_instance_field_value(self):
        test = Category(name="test")
        blog = Blog(category=test, title="Python")

        self.assertEqual(get_instance_field_value(Category(), "content"), None)
        self.assertEqual(get_instance_field_value(test, "name"), "test")
        self.assertEqual(get_instance_field_value(blog, "category__name"), "test")
        self.assertEqual(get_instance_field_value(blog, "category__color"), None)
