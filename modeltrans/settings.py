from django.conf import settings

DEBUG = getattr(settings, 'MODELTRANS_DEBUG', False)

DEFAULT_LANGUAGE = 'en'
ENABLE_REGISTRATIONS = True

AVAILABLE_LANGUAGES = ('nl', 'de', 'fr')
