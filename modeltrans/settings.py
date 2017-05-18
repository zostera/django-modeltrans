from django.conf import settings

DEBUG = getattr(settings, 'MODELTRANS_DEBUG', False)

DEFAULT_LANGUAGE = settings.DEFAULT_LANGUAGE or 'en'
ENABLE_REGISTRATIONS = settings.ENABLE_REGISTRATIONS or True

AVAILABLE_LANGUAGES = settings.AVAILABLE_LANGUAGES or ('nl', 'de', 'fr')
