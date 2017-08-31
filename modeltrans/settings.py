from django.conf import settings

LANGUAGE_CODE = settings.LANGUAGE_CODE

# list of available languages for modeltrans translations.
# defaults to the list of language codes extracted from django setting LANGUAGES
MODELTRANS_AVAILABLE_LANGUAGES = tuple(set(getattr(
    settings,
    'MODELTRANS_AVAILABLE_LANGUAGES',
    [language_code for language_code, verbose_name in getattr(settings, 'LANGUAGES') if language_code != LANGUAGE_CODE]
)))
