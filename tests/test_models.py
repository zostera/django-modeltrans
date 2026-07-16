from django.core.exceptions import ValidationError
from django.db import DataError, models, transaction
from django.test import TestCase, override_settings
from django.utils.translation import override

from modeltrans.fields import TranslationField

from .app.models import (
    Article,
    Blog,
    Challenge,
    ChallengeContent,
    ChildArticle,
    Department,
    NullableTextModel,
    Organization,
    TaggedBlog,
    TextModel,
)
from modeltrans.manager import transform_translatable_fields

from .utils import CreateTestModel


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

    @override_settings(
        MODELTRANS_AVAILABLE_LANGUAGES=("de", "en", "nl", "fr"),
        MODELTRANS_FALLBACK={"default": ("nl",)},
    )
    def test_get_has_no_translation_fallback_to_local_default_language(self):
        org = Organization(language="de", name="das foo", i18n={"name_en": "bar"})
        # en is activated and name_en is present
        self.assertEqual(org.name_i18n, "bar")
        with override("fr"):
            # fr is activated but name_fr is not present and neither is name_nl (from the fallback chain)
            self.assertEqual(org.name_i18n, "das foo")

    @override_settings(
        MODELTRANS_AVAILABLE_LANGUAGES=("de", "en", "nl", "fr"),
        MODELTRANS_FALLBACK={"default": ("nl",)},
    )
    def test_get_has_no_translation_fallback_to_fallback_chain_despite_local_default_language(self):
        org = Organization(language="de", name="das foo", i18n={"name_en": "bar", "name_nl": "foo"})
        # en is activated and name_en is present
        self.assertEqual(org.name_i18n, "bar")
        with override("fr"):
            # fr is activated and name_fr is not present, but name_nl is (from the fallback chain)
            self.assertEqual(org.name_i18n, "foo")

    @override_settings(
        MODELTRANS_AVAILABLE_LANGUAGES=("en", "de", "nl"),
        MODELTRANS_FALLBACK={"default": ("en",)},
    )
    def test_default_language_field_with_fallback_language_field(self):
        class Model(models.Model):
            title = models.CharField(max_length=10)
            language = models.CharField(max_length=2)
            i18n = TranslationField(
                fields=["title"],
                default_language_field="language",
                fallback_language_field="language",
            )

            class Meta:
                app_label = "test"

        with CreateTestModel(Model, translate=True):
            m = Model(language="nl", title="foo", title_en="bar")

        with override("de"):
            # Fall back to language in `fallback_language_field` and not to languages in fallback chain
            self.assertEqual(m.title_i18n, "foo")

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

    def test_fallback_getting_JSONField(self):
        m = TaggedBlog.objects.create(title="Falcon", tags=["bird", "raptor"])
        with override("de"):
            # tags_de is not set, return fallback
            self.assertEqual(m.tags_i18n, ["bird", "raptor"])

        m = TaggedBlog.objects.create(title="Falcon", tags_fr=[])
        with override("fr"):
            # tags_fr is set, return the empty list
            self.assertEqual(m.tags_i18n, [])

        m = TaggedBlog.objects.create(title="Falcon", tags_fr=None)
        with override("fr"):
            # tags_fr is set to None, return field default (which is
            # an empty list)
            self.assertEqual(m.tags_i18n, [])

    def test_creating_using_virtual_default_language_field(self):
        m = Blog.objects.create(title_en="Falcon")

        self.assertEqual(m.title, "Falcon")

    def test_creating_using_virtual_local_default_language_field(self):
        org = Organization.objects.create(language="de", name_de="foo")
        self.assertEqual(org.name, "foo")

    def test_creating_using_virtual_local_default_language_field_on_related_model(self):
        org = Organization.objects.create(language="de", name_de="foo")
        dept = Department.objects.create(organization=org, name_de="bar")
        self.assertEqual(dept.name, "bar")

    def test_creating_prevents_double_definition(self):
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
        expected_message = "Blog() got unexpected keyword arguments: 'name'"
        with self.assertRaisesMessage(TypeError, expected_message):
            Blog.objects.create(name="Falcon")

        expected_message = "Blog() got unexpected keyword arguments: 'name_nl'"
        with self.assertRaisesMessage(TypeError, expected_message):
            Blog.objects.create(title="Falcon", name_nl="Valk")

    def test_clean_required_languages_list(self):
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

    def test_clean_required_languages_dict(self):
        class Model(models.Model):
            title = models.CharField(max_length=10)
            i18n = TranslationField(fields=["title"], required_languages={"title": ["nl", "de"]})

            class Meta:
                app_label = "test"

        with CreateTestModel(Model, translate=True):
            m = Model(title_nl="foo", title="bar")

        with self.assertRaises(ValidationError) as e:
            m.full_clean()

        self.assertEqual(
            {(field, tuple(errors)) for field, errors in e.exception},
            {("title_de", ("This field cannot be null.",))},
        )

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


class CustomFallbackLanguageTest(TestCase):
    def test_instance_fallback(self):
        instance = Challenge(default_language="nl", title="Hurray", i18n={"title_nl": "Hoera"})

        with override("de"):
            self.assertEqual(instance.title_i18n, "Hoera")
        with override("en"):
            self.assertEqual(instance.title_i18n, "Hurray")
        with override("nl"):
            self.assertEqual(instance.title_i18n, "Hoera")

    def test_empty_original_field(self):
        instance = Challenge(default_language="nl", title="", i18n={"title_nl": "Hoera"})

        with override("de"):
            self.assertEqual(instance.title_i18n, "Hoera")
        with override("en"):
            self.assertEqual(instance.title_i18n, "Hoera")

    def test_instance_fallback_follow_relation(self):
        challenge = Challenge.objects.create(default_language="nl", title="Hurray")
        content = ChallengeContent(
            challenge=challenge, content="Congratulations", i18n={"content_nl": "Gefeliciteerd"}
        )

        with override("de"):
            self.assertEqual(content.content_i18n, "Gefeliciteerd")
        with override("en"):
            self.assertEqual(content.content_i18n, "Congratulations")
        with override("nl"):
            self.assertEqual(content.content_i18n, "Gefeliciteerd")

    def test_instance_fallback_without_related_instance(self):
        content = ChallengeContent(content="Congratulations", i18n={"content_nl": "Gefeliciteerd"})
        self.assertEqual(content.content_nl, "Gefeliciteerd")
        self.assertEqual(content.content_en, "Congratulations")

        with override("de"):
            self.assertEqual(content.content_i18n, "Congratulations")
        with override("en"):
            self.assertEqual(content.content_i18n, "Congratulations")
        with override("nl"):
            self.assertEqual(content.content_i18n, "Gefeliciteerd")


class TranslatedFieldInheritanceTest(TestCase):
    def test_child_model_i18n_fields(self):
        self.assertFalse(hasattr(Article, "child_title_nl"))
        self.assertTrue(hasattr(ChildArticle, "child_title_nl"))

    def test_child_model_required_languages(self):
        self.assertTrue(Article._meta.get_field("title_nl").blank)
        self.assertFalse(ChildArticle._meta.get_field("title_nl").blank)

    def test_diff_i18n_parent_child_models_instances(self):
        """
        Test different behavior of Article and ChildArticle instances
        """
        article = Article(title="Title")
        article.full_clean()
        article.save()
        child_article = ChildArticle(title="Title", child_title="Child title")
        with self.assertRaises(ValidationError):
            child_article.full_clean()
        child_article.title_nl = "Title NL"
        child_article.child_title_nl = "Child title NL"
        child_article.full_clean()
        child_article.save()
        self.assertFalse("child_title_nl" in article.i18n)
        self.assertTrue("child_title_nl" in child_article.i18n)


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


class ForeignKeyAttnameResolutionTest(TestCase):
    """
    Test that transform_translatable_fields resolves FK objects when kwargs
    use attname (e.g., organization_id) instead of field name (organization).

    This happens when models are constructed from serialized or deserialized
    data where ForeignKey fields are stored by column name rather than field
    name.
    """

    def test_fk_attname_resolves_default_language(self):
        """Department with organization_id should resolve Organization to get its language."""
        org = Organization.objects.create(language="de", name="Das Org")
        dept = Department(organization_id=org.pk, name_de="Abteilung")
        self.assertEqual(dept.name, "Abteilung")

    def test_fk_field_name_still_works(self):
        """Department with organization=obj should still work as before."""
        org = Organization.objects.create(language="de", name="Das Org")
        dept = Department(organization=org, name_de="Abteilung")
        self.assertEqual(dept.name, "Abteilung")

    def test_fk_attname_non_default_language_stored_in_i18n(self):
        """Non-default language values should be stored in i18n even with FK attname."""
        org = Organization.objects.create(language="de", name="Das Org")
        result = transform_translatable_fields(
            Department, {"organization_id": org.pk, "name": "German Name", "name_nl": "Dutch Name"}
        )
        self.assertEqual(result["name"], "German Name")
        self.assertEqual(result["i18n"]["name_nl"], "Dutch Name")

    def test_fk_attname_with_missing_fk_falls_back(self):
        """When FK id points to a nonexistent object, default_language is None."""
        result = transform_translatable_fields(
            Department, {"organization_id": 999999, "name": "Fallback"}
        )
        # The original field is passed through; virtual fields for None language are
        # stored in i18n since they don't match the (None) default language.
        self.assertEqual(result["name"], "Fallback")


class DuplicateOriginalAndVirtualFieldTest(TestCase):
    """
    Test behavior when both the original field and a translated virtual field
    for the default language are present in kwargs.

    This happens when constructing model instances from deserialized data that
    includes both the DB column value and the virtual field values.
    """

    def test_same_values_tolerated(self):
        """Identical original and virtual field values should not raise."""
        result = transform_translatable_fields(
            Blog, {"title": "Falcon", "title_en": "Falcon"}
        )
        self.assertEqual(result["title"], "Falcon")

    def test_both_falsy_tolerated(self):
        """Empty string + None are both falsy and should be tolerated."""
        result = transform_translatable_fields(
            Blog, {"title": "", "title_en": None}
        )
        self.assertEqual(result["title"], "")

    def test_both_none_tolerated(self):
        """Both None should be tolerated."""
        result = transform_translatable_fields(
            Blog, {"title": None, "title_en": None}
        )
        self.assertIsNone(result["title"])

    def test_different_values_raises(self):
        """Different original and virtual field values should still raise ValueError."""
        with self.assertRaisesMessage(
            ValueError,
            'Attempted override of "title" with "title_en". Only one of the two is allowed.',
        ):
            transform_translatable_fields(
                Blog, {"title": "Falcon", "title_en": "Hawk"}
            )

    def test_original_value_takes_precedence(self):
        """When values are compatible, the original field value is kept."""
        result = transform_translatable_fields(
            Blog, {"title": "Falcon", "title_en": "Falcon", "title_nl": "Valk"}
        )
        self.assertEqual(result["title"], "Falcon")
        self.assertEqual(result["i18n"]["title_nl"], "Valk")

    def test_with_local_default_language_field(self):
        """Duplicate tolerance works with per-instance default_language_field."""
        org = Organization.objects.create(language="de", name="Das Org")
        result = transform_translatable_fields(
            Department,
            {"organization_id": org.pk, "name": "Abteilung", "name_de": "Abteilung"},
        )
        self.assertEqual(result["name"], "Abteilung")

    def test_with_local_default_language_field_different_raises(self):
        """Different values with per-instance default_language_field should raise."""
        org = Organization.objects.create(language="de", name="Das Org")
        with self.assertRaises(ValueError):
            transform_translatable_fields(
                Department,
                {"organization_id": org.pk, "name": "Abteilung", "name_de": "Büro"},
            )
