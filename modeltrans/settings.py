from django.conf import settings

DEBUG = getattr(settings, 'MODELTRANS_DEBUG', False)

DEFAULT_LANGUAGE = getattr(settings, 'DEFAULT_LANGUAGE', 'en')
ENABLE_REGISTRATIONS = getattr(settings, 'ENABLE_REGISTRATIONS', True)

AVAILABLE_LANGUAGES = getattr(settings, 'AVAILABLE_LANGUAGES', ('nl', 'de', 'fr'))
