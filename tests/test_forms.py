from django import forms
from django.forms import ModelForm, modelform_factory
from django.test import TestCase
from django.utils.translation import override

from modeltrans.conf import get_default_language
from modeltrans.forms import TranslationModelForm

from .app.models import Blog, Challenge, Comment, Post


class ModelFormTest(TestCase):
    def test_modelform(self):
        class BlogForm(ModelForm):
            class Meta:
                model = Blog
                fields = ("title_i18n", "body_i18n")

        article = Blog(title="English", title_nl="Nederlands")

        with override("nl"):
            form = BlogForm(
                instance=article, data={"title_i18n": "Nederlandse taal", "body_i18n": "foo"}
            )
            form.save()

        article.refresh_from_db()
        self.assertEqual(article.title_nl, "Nederlandse taal")
        self.assertEqual(article.title_en, "English")

        with override("en"):
            form = BlogForm(
                instance=article, data={"title_i18n": "English language", "body_i18n": "foo"}
            )
            form.save()

        article.refresh_from_db()
        self.assertEqual(article.title_nl, "Nederlandse taal")
        self.assertEqual(article.title_en, "English language")


class Form(TranslationModelForm):
    """Challenge form."""

    start_date = forms.DateField(label="start date")
    end_date = forms.DateField(label="end date")

    class Meta:
        model = Challenge
        fields = ["title", "start_date", "default_language", "header"]
        required = {"title": True, "header": False}


class ExcludeForm(TranslationModelForm):
    """Challenge form."""

    start_date = forms.DateField(label="start date")
    end_date = forms.DateField(label="end date")

    field_order = ["start_date", "title", "end_date"]  # test the custom field_order setting

    class Meta:
        model = Challenge
        exclude = ["header", "default_language"]
        languages = ["browser", "de", "fallback"]
        fallback_language = "fr"
        widgets = {"title": forms.widgets.Textarea}


class TranslationModelFormTestCase(TestCase):
    def test_languages_errors(self):
        """Test the error messages for incorrect languages options."""

        for language in [0, "es_it", "e", "xx"]:
            with self.assertRaisesMessage(
                ValueError, f"languages: value {language} is not permitted"
            ):
                Form(languages=[language])

        class NoLanguageForm(TranslationModelForm):
            """Challenge form where fallback can be edited."""

            class Meta:
                model = Challenge
                fields = ["title", "header"]
                languages = []

        with self.assertRaisesMessage(ValueError, "languages: No languages have been defined."):
            NoLanguageForm()

    def test_defaults(self):
        """Test the default form options."""
        form = Form()
        self.assertEqual(form.languages, ["browser", "fallback"])
        self.assertEqual(form.fallback_language, get_default_language())

    def test_get_fallback_language(self):
        """Test that the form fallback language is set correctly."""

        with self.subTest("Test the default fallback_language"):
            form = Form()
            self.assertEqual(form.fallback_language, "en")

        with self.subTest("Test the fallback defined in Meta options"):
            form = ExcludeForm()
            self.assertEqual(form.fallback_language, "fr")

        challenge = Challenge.objects.create(default_language="de")
        with self.subTest("Test the fallback defined in a model instance"):
            form = Form(instance=challenge)
            self.assertEqual(form.fallback_language, "de")

        with self.subTest("Verify the Meta option overrides the model instance"):
            form = ExcludeForm(instance=challenge)
            self.assertEqual(form.fallback_language, "fr")

        with self.subTest("Test the fallback defined in form parameter"):
            form = Form(fallback_language="de")
            self.assertEqual(form.fallback_language, "de")

            # test that it overrides the Meta option
            form = ExcludeForm(fallback_language="nl")
            self.assertEqual(form.fallback_language, "nl")

    def test_fields_defined_with_fields_option(self):
        """Tests fields and their order defined with Meta 'fields' option."""
        form = Form()
        self.assertEqual(form.language_codes, ["en"])
        self.assertEqual(
            list(form.fields.keys()),
            ["title", "start_date", "default_language", "header", "end_date"],
        )

    def test_fields_defined_with_fields_option_explicit_naming_of_default_field(self):
        """Test that the default language fields is not repeated."""

        class BadForm(TranslationModelForm):
            class Meta:
                model = Challenge
                fields = ("title", "title_en", "header")

        form = BadForm()
        self.assertEqual(list(form.fields.keys()), ["title", "header"])

    def test_fields_defined_with_fields_option_tuple(self):
        """Test that form works correctly even if fields is defined in tuple format."""

        class TupleForm(TranslationModelForm):
            class Meta:
                model = Challenge
                fields = ("title", "header")

        form = TupleForm()
        self.assertEqual(list(form.fields.keys()), ["title", "header"])

    def test_fields_with_languages_kwarg_and_fields_option(self):
        """Test fields and their order defined with parameter override of in form with 'fields' option."""
        form = Form(languages=["fr", "fallback"])
        self.assertEqual(form.language_codes, ["fr", "en"])
        self.assertEqual(
            list(form.fields.keys()),
            [
                "title_fr",
                "title",
                "start_date",
                "default_language",
                "header_fr",
                "header",
                "end_date",
            ],
        )

    def test_fields_defined_with_exclude_options(self):
        """Test fields and their order defined with Meta 'exclude' option."""
        form = ExcludeForm()
        self.assertEqual(form.language_codes, ["en", "de", "fr"])
        self.assertEqual(
            list(form.fields.keys()), ["start_date", "title", "title_de", "title_fr", "end_date"]
        )

    def test_fields_defined_with_exclude_option_tuple(self):
        """Test that form works correctly even if fields is defined in tuple format."""

        class TupleForm(TranslationModelForm):
            class Meta:
                model = Challenge
                exclude = ("default_language",)

        form = TupleForm()
        self.assertEqual(list(form.fields.keys()), ["title", "header"])

    def test_fields_with_languages_kwarg_with_exclude_option(self):
        """Test fields and their order with parameter override in form with 'exclude' option."""
        form = ExcludeForm(languages=["de", "fallback"], fallback_language="nl")
        self.assertEqual(form.language_codes, ["de", "nl"])
        self.assertEqual(
            list(form.fields.keys()), ["start_date", "title_de", "title_nl", "end_date"]
        )

    def test_fields_with_model_instance_fallback_with_exclude_options(self):
        """Test fields and their order with model instance fallback override in form with 'exclude' option."""
        challenge = Challenge.objects.create(default_language="nl")
        form = ExcludeForm(instance=challenge)
        self.assertEqual(form.language_codes, ["en", "de", "fr"])
        self.assertEqual(
            list(form.fields.keys()), ["start_date", "title", "title_de", "title_fr", "end_date"]
        )

    def test_fields_with_fallback_language_kwarg_with_exclude_option(self):
        """Test fields and their order with parameter override of model instance fallback in form with 'exclude'."""
        challenge = Challenge(default_language="de")
        form = ExcludeForm(instance=challenge, fallback_language="nl")
        self.assertEqual(form.language_codes, ["en", "de", "nl"])
        self.assertEqual(
            list(form.fields.keys()), ["start_date", "title", "title_de", "title_nl", "end_date"]
        )

    def test_setting_of_field_properties(self):
        """Test that fields are set with the correct properties."""
        with self.subTest("Browser (fallback) language"):
            title_field = Form().fields["title"]
            self.assertEqual(title_field.label, "Title (EN, default language)")
            self.assertTrue(title_field.required)

        with self.subTest("Custom (fallback) language"):
            form = ExcludeForm()

            title_field = form.fields["title"]
            self.assertEqual(title_field.label, "Title (EN, translation language)")
            self.assertEqual(title_field.required, False)
            self.assertEqual(title_field.widget.__class__, forms.widgets.Textarea)

            title_de_field = form.fields["title_de"]
            self.assertEqual(title_de_field.label, "Title (DE, translation language)")
            self.assertEqual(title_de_field.required, False)
            self.assertEqual(title_de_field.widget.__class__, forms.widgets.Textarea)

            title_fr_field = form.fields["title_fr"]
            self.assertEqual(title_fr_field.label, "Title (FR, default language)")
            self.assertEqual(title_fr_field.required, True)
            self.assertEqual(title_fr_field.widget.__class__, forms.widgets.Textarea)

    def test_translated_field_labels(self):
        """Test that a field's verbose_name is translated to the currently active language."""
        form_cls = modelform_factory(Post, fields="__all__")
        form = form_cls()
        self.assertEqual(form.fields["title"].label, "Title of the post")
        self.assertEqual(form.fields["title_de"].label, "Title of the post (DE)")
        self.assertEqual(form.fields["title_fr"].label, "Title of the post (FR)")

        with override("de"):
            form = form_cls()
            self.assertEqual(form.fields["title"].label, "Titel des Beitrags")
            self.assertEqual(form.fields["title_de"].label, "Titel des Beitrags (DE)")
            self.assertEqual(form.fields["title_fr"].label, "Titel des Beitrags (FR)")

        with override("fr"):
            form = form_cls()
            self.assertEqual(form.fields["title"].label, "Titre de l'article")
            self.assertEqual(form.fields["title_de"].label, "Titre de l'article (DE)")
            self.assertEqual(form.fields["title_fr"].label, "Titre de l'article (FR)")

    def test_form_initial_values(self):
        challenge = Challenge.objects.create(title="english", title_fr="french")
        initial_data = {
            "title": "not english",
            "title_fr": "not french",
            "header_fr": "fr header",
        }

        with self.subTest("Initial values from model instance"):
            form = Form(instance=challenge, languages=["fr", "fallback"])

            self.assertEqual(form["title"].initial, challenge.title)
            self.assertEqual(form["title_fr"].initial, challenge.title_fr)
            self.assertEqual(form["header"].initial, challenge.header)
            self.assertEqual(form["header_fr"].initial, challenge.header_fr)
            self.assertEqual(form["default_language"].initial, challenge.default_language)

        with self.subTest("Initial values from initial data"):
            form = Form(initial=initial_data, languages=["fr", "fallback"])

            self.assertEqual(form["title"].initial, initial_data["title"])
            self.assertEqual(form["title_fr"].initial, initial_data["title_fr"])
            # Empty initial data is always None
            self.assertEqual(form["header"].initial, None)
            self.assertEqual(form["header_fr"].initial, initial_data["header_fr"])
            self.assertEqual(form["default_language"].initial, get_default_language())

        with self.subTest("Initial values from initial data model override"):
            form = Form(initial=initial_data, instance=challenge, languages=["fr", "fallback"])

            self.assertEqual(form["title"].initial, initial_data["title"])
            self.assertEqual(form["title_fr"].initial, initial_data["title_fr"])
            self.assertEqual(form["header"].initial, "")
            self.assertEqual(form["header_fr"].initial, initial_data["header_fr"])
            self.assertEqual(form["default_language"].initial, get_default_language())

    def test_form_valid_and_save(self):
        with self.subTest("No translations and header not required."):
            data = {"start_date": "2021-01-01", "end_date": "2021-02-02", "title": "A title"}
            form = Form(data=data)
            self.assertTrue(form.is_valid())
            challenge = form.save()
            self.assertEqual(challenge.title, data["title"])
            self.assertEqual(challenge.header, "")

            data = {"start_date": "2021-01-01", "end_date": "2021-02-02", "title_fr": "Un title"}
            form = ExcludeForm(data=data)
            self.assertTrue(form.is_valid())
            challenge = form.save()
            self.assertEqual(challenge.title, "")
            self.assertEqual(challenge.title_fr, data["title_fr"])
            self.assertEqual(challenge.header, "")

        with self.subTest("Test that only fallback is required"):
            data = {"start_date": "2021-01-01", "end_date": "2021-02-02"}

            form = Form(data=data, languages=["de", "fr", "nl"], fallback_language="nl")
            form.is_valid()
            self.assertEqual(form.errors, {"title_nl": ["This field is required."]})

            form = ExcludeForm(data=data, languages=["de", "en", "fallback"])
            form.is_valid()
            self.assertEqual(form.errors, {"title_fr": ["This field is required."]})

        with self.subTest("Test that translations are stored correctly"):
            data = {
                "start_date": "2021-01-01",
                "end_date": "2021-02-02",
                "title_nl": "Een titel",
                "title_de": "Ein titel",
            }
            form = Form(data=data, languages=["de", "fr", "nl"], fallback_language="nl")
            self.assertTrue(form.is_valid())
            challenge = form.save()
            self.assertEqual(challenge.title_nl, data["title_nl"])
            self.assertEqual(challenge.title_de, data["title_de"])
            self.assertEqual(challenge.title_fr, "")
            self.assertEqual(challenge.title, "")
            self.assertEqual(challenge.header, "")

            data = {
                "start_date": "2021-01-01",
                "end_date": "2021-02-02",
                "title_nl": "Een titel",
                "title_fr": "Un titel",
            }
            form = ExcludeForm(data=data, languages=["de", "nl", "fallback"])
            self.assertTrue(form.is_valid())
            challenge = form.save()
            self.assertEqual(challenge.title_nl, data["title_nl"])
            self.assertEqual(challenge.title_fr, data["title_fr"])
            self.assertEqual(challenge.title_de, "")
            self.assertEqual(challenge.title, "")
            self.assertEqual(challenge.header, "")

        with self.subTest("Update existing instance"):
            challenge = Challenge.objects.create(
                title="english", title_fr="french", default_language="fr"
            )

            data = {
                "start_date": "2021-01-01",
                "end_date": "2021-02-02",
                "title_nl": "Een titel",
                "title_de": "Ein titel",
            }
            form = Form(instance=challenge, data=data, languages=["nl", "de"])
            self.assertTrue(form.is_valid())
            form.save()
            self.assertEqual(challenge.title_nl, data["title_nl"])
            self.assertEqual(challenge.title_de, data["title_de"])

            data = {
                "start_date": "2021-01-01",
                "end_date": "2021-02-02",
                "title_nl": "Een andere titel",
                "title_fr": "Un titel nouveau",
            }
            form = ExcludeForm(instance=challenge, data=data, languages=["nl", "fallback"])
            self.assertTrue(form.is_valid())
            form.save()
            self.assertEqual(challenge.title_nl, data["title_nl"])
            self.assertEqual(challenge.title_fr, data["title_fr"])

    def test_limit_choices_to(self):
        published_post = Post.objects.create(title="foo", is_published=True)
        unpublished_post = Post.objects.create(title="bar", is_published=False)
        form_class = modelform_factory(Comment, fields="__all__")
        form = form_class()
        queryset = form.fields["post"].queryset
        self.assertEqual(queryset.count(), 1)
        self.assertIn(published_post, queryset)
        self.assertNotIn(unpublished_post, queryset)
