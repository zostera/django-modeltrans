from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from modeltrans.conf import check_fallback_chain, get_available_languages_setting
from modeltrans.translator import check_languages, get_i18n_field, get_i18n_field_param

from .app.models import Person


class FallbackConfTest(TestCase):
    @override_settings(MODELTRANS_FALLBACK={"fy": ("nl", "en")})
    def test_fallback_must_have_default(self):
        message = "MODELTRANS_FALLBACK setting must have a `default` key."

        with self.assertRaisesMessage(ImproperlyConfigured, message):
            check_fallback_chain()

    @override_settings(
        MODELTRANS_AVAILABLE_LANGUAGES=("nl", "en"),
        MODELTRANS_FALLBACK={"default": ("en",), "fy": ("nl", "en")},
    )
    def test_fallback_must_use_available_languages_as_key(self):
        message = "MODELTRANS_FALLBACK contains language `fy` which is not in MODELTRANS_AVAILABLE_LANGUAGES"

        with self.assertRaisesMessage(ImproperlyConfigured, message):
            check_fallback_chain()

    @override_settings(
        MODELTRANS_AVAILABLE_LANGUAGES=("fy", "nl", "en"),
        MODELTRANS_FALLBACK={"default": ("en",), "fy": ("nl", "fr", "en")},
    )
    def test_fallback_must_use_available_languages_in_chain(self):
        message = "MODELTRANS_FALLBACK contains language `fr` which is not in MODELTRANS_AVAILABLE_LANGUAGES"

        with self.assertRaisesMessage(ImproperlyConfigured, message):
            check_fallback_chain()

    @override_settings(MODELTRANS_AVAILABLE_LANGUAGES=(("nl", "Dutch"), ("en", "English")))
    def test_available_languages_should_be_str(self):
        message = "MODELTRANS_AVAILABLE_LANGUAGES should be an iterable of strings"
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            get_available_languages_setting()


class DefaultLanguageConfTest(TestCase):
    @override_settings(
        LANGUAGE_CODE="es", MODELTRANS_AVAILABLE_LANGUAGES=("nl", "de", "fr")
    )
    def test_django_language_code_not_available_language(self):
        message = 'Language "en" is in required_languages on Model "Person" but not in settings.MODELTRANS_AVAILABLE_LANGUAGES.'
        i18n_field = get_i18n_field(Person)
        required_languages = get_i18n_field_param(
            Person, i18n_field, "required_languages"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            check_languages(required_languages, Person)

    @override_settings(
        LANGUAGE_CODE="es",
        MODELTRANS_DEFAULT_LANGUAGE="en",
        MODELTRANS_AVAILABLE_LANGUAGES=("nl", "de", "fr"),
    )
    def test_default_language_code_is_available_language(self):
        i18n_field = get_i18n_field(Person)
        required_languages = get_i18n_field_param(
            Person, i18n_field, "required_languages"
        )
        check_languages(required_languages, Person)
