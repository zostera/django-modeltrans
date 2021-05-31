from django import forms
from django.forms import ModelForm
from django.test import TestCase
from django.utils.translation import override

from modeltrans.conf import get_default_language
from modeltrans.forms import TranslationModelForm

from .app.models import Blog, Challenge


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
        fields = [
            "title",
            "start_date",
            "default_language",
            "header",
        ]  # adding start_date to test the ordering
        required = {"title": True, "header": False}


class ExcludeForm(TranslationModelForm):
    """Challenge form."""

    start_date = forms.DateField(label="start date")
    end_date = forms.DateField(label="end date")

    field_order = ["start_date", "title", "end_date"]  # test the custom field_order setting

    class Meta:
        model = Challenge
        exclude = ["header", "default_language"]
        included_languages = ["browser", "de", "fallback"]
        fallback_language = "fr"
        # TODO FUTURE: fallback_readonly = True
        widgets = {"title": forms.widgets.Textarea}  # add widget to test field setting


class TranslationFormTestCase(TestCase):
    def test_included_languages_errors(self):
        """Test the error messages for incorrect included_languages options."""

        # TODO FUTURE at later stage
        # with self.assertRaisesMessage(
        #    ValueError, "included languages: you cannot include other options when including 'all'"
        # ):
        #    Form(included_languages=["all", "fallback"])

        with self.assertRaisesMessage(ValueError, "included_languages: options should be strings"):
            Form(included_languages=[0, "fallback"])

        with self.assertRaisesMessage(
            ValueError, "included_languages: option es_it is not permitted"
        ):
            Form(included_languages=["es_it", "fallback"])

        with self.assertRaisesMessage(ValueError, "included_languages: option e is not permitted"):
            Form(included_languages=["e", "fallback"])

        with self.assertRaisesMessage(
            ValueError, "included_languages: xx is not an available language in the system"
        ):
            Form(included_languages=["xx", "fallback"])

        class NoLanguageForm(TranslationModelForm):
            """Challenge form where fallback can be edited."""

            class Meta:
                model = Challenge
                fields = ["title", "header"]
                included_languages = []

        with self.assertRaisesMessage(
            ValueError, "included_languages: Error. No languages have been defined."
        ):
            NoLanguageForm()

    def test_defaults(self):
        """Test the default form options."""
        form = Form()
        self.assertEqual(form.included_languages, ["browser"])
        self.assertEqual(form.fallback_language, get_default_language())
        # TODO FUTURE self.assertEqual(form.fallback_readonly, True)

    def test_get_fallback_language(self):
        """Test that the form fallback language is set correctly."""

        with self.subTest("Test the default fallback_language"):
            form = Form()
            self.assertEqual(form.fallback_language, get_default_language())

        with self.subTest("Test the fallback defined in Meta options"):
            form = ExcludeForm()
            self.assertEqual(form.fallback_language, "fr")

        with self.subTest("Test the fallback defined in a model instance"):
            challenge = Challenge.objects.create(default_language="de")

            form = Form(instance=challenge)
            self.assertEqual(form.fallback_language, "de")

            # test that it override the Meta option
            form = ExcludeForm(instance=challenge)
            self.assertEqual(form.fallback_language, "de")

        with self.subTest("Test the fallback defined in form parameter"):
            form = Form(fallback_language="de")
            self.assertEqual(form.fallback_language, "de")

            # test that it overrides the Meta option
            form = ExcludeForm(fallback_language="de")
            self.assertEqual(form.fallback_language, "de")

    def test_fields_defined_with_fields_option(self):
        """Tests fields and their order defined with Meta 'fields' option."""
        form = Form()
        self.assertEqual(form.languages, ["en"])
        self.assertEqual(
            list(form.fields.keys()),
            ["title", "start_date", "default_language", "header", "end_date"],
        )

    def test_fields_with_included_languages_kwarg_and_fields_option(self):
        """Test fields and their order defined with parameter override of in form with 'fields' option."""
        form = Form(included_languages=["fr", "fallback"])
        self.assertEqual(form.languages, ["fr", "en"])
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
        self.assertEqual(form.languages, ["en", "de", "fr"])
        self.assertEqual(
            list(form.fields.keys()), ["start_date", "title", "title_de", "title_fr", "end_date"]
        )

    def test_fields_with_included_languages_kwarg_with_exclude_option(self):
        """Test fields and their order with parameter override in form with 'exclude' option."""
        form = ExcludeForm(included_languages=["de", "fallback"], fallback_language="nl")
        self.assertEqual(form.languages, ["de", "nl"])
        self.assertEqual(
            list(form.fields.keys()), ["start_date", "title_de", "title_nl", "end_date"]
        )

    def test_fields_with_model_instance_fallback_with_exclude_options(self):
        """Test fields and their order with model instance fallback override in form with 'exclude' option."""
        challenge = Challenge.objects.create(default_language="nl")
        form = ExcludeForm(instance=challenge)
        self.assertEqual(form.languages, ["en", "de", "nl"])
        self.assertEqual(
            list(form.fields.keys()), ["start_date", "title", "title_de", "title_nl", "end_date"]
        )

    def test_fields_with_fallback_language_kwarg_with_exclude_option(self):
        """Test fields and their order with parameter override of model instance fallback in form with 'exclude'."""
        challenge = Challenge(default_language="de")
        form = ExcludeForm(instance=challenge, fallback_language="nl")
        self.assertEqual(form.languages, ["en", "de", "nl"])
        self.assertEqual(
            list(form.fields.keys()), ["start_date", "title", "title_de", "title_nl", "end_date"]
        )

    def test_setting_of_field_properties(self):
        """Test that fields are set with the correct properties."""
        with self.subTest("Browser (fallback) language"):
            form = Form()

            title_field = form.fields["title"]
            self.assertEqual(title_field.label, "Title (EN, default language)")
            self.assertEqual(title_field.required, True)

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

    def test_form_initial_values(self):
        challenge = Challenge(title="english", title_fr="espanol")
        challenge = Challenge.objects.create(title="english", title_fr="espanol")
        initial_data = {
            "title": "not english",
            "title_fr": "not espenaol",
            "header_fr": "fr header",
        }

        with self.subTest("Initial values from model instance"):
            form = Form(instance=challenge, included_languages=["fr", "fallback"])

            self.assertEqual(form["title"].initial, challenge.title)
            self.assertEqual(form["title_fr"].initial, challenge.title_fr)
            self.assertEqual(form["header"].initial, challenge.header)
            self.assertEqual(form["header_fr"].initial, challenge.header_fr)
            self.assertEqual(form["default_language"].initial, challenge.default_language)

        with self.subTest("Initial values from initial data"):
            form = Form(initial=initial_data, included_languages=["fr", "fallback"])

            self.assertEqual(form["title"].initial, initial_data["title"])
            self.assertEqual(form["title_fr"].initial, initial_data["title_fr"])
            self.assertIsNone(form["header"].initial)
            self.assertEqual(form["header_fr"].initial, initial_data["header_fr"])
            self.assertEqual(form["default_language"].initial, get_default_language())

        with self.subTest("Initial values from initial data model override"):
            form = Form(
                initial=initial_data, instance=challenge, included_languages=["fr", "fallback"]
            )

            self.assertEqual(form["title"].initial, initial_data["title"])
            self.assertEqual(form["title_fr"].initial, initial_data["title_fr"])
            self.assertEqual(form["header"].initial, "")
            self.assertEqual(form["header_fr"].initial, initial_data["header_fr"])
            self.assertEqual(form["default_language"].initial, get_default_language())


# TODO test form valid and save and instance creation and update.
