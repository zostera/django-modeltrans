from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from modeltrans.conf import (
    check_fallback_chain,
    check_lang_code_duplicates,
    get_available_languages,
    get_available_languages_setting,
)


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

    @override_settings(MODELTRANS_AVAILABLE_LANGUAGES=("nl", "nl", "de"))
    def test_lang_code_duplicates_validation(self):
        message = (
            "MODELTRANS_AVAILABLE_LANGUAGES or LANGUAGES should not contain duplicates, current list: {}"
        ).format(get_available_languages())
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            check_lang_code_duplicates()

    @override_settings(MODELTRANS_AVAILABLE_LANGUAGES=("nl", "bg", "ar"), LANGUAGE_CODE="en")
    def test_languages_ordering(self):
        self.assertEqual(("en", "nl", "bg", "ar"), get_available_languages())
        self.assertEqual(("nl", "bg", "ar"), get_available_languages(include_default=False))
