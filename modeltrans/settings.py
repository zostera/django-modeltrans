from django.conf import settings

DEBUG = getattr(settings, 'MODELTRANS_DEBUG', False)

# replace by reading from django setting LANGUAGE_CODE
DEFAULT_LANGUAGE = getattr(settings, 'DEFAULT_LANGUAGE', 'en')

# default to the list of language codes extracted from django setting LANGUAGES
MODELTRANS_AVAILABLE_LANGUAGES = getattr(
    settings,
    'MODELTRANS_AVAILABLE_LANGUAGES',
    [language_code for language_code, verbose_name in getattr(settings, 'LANGUAGES')]
)
