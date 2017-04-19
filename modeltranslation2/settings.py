from django.conf import settings

DEBUG = getattr(settings, 'MODELTRANSLATION_DEBUG', False)

ENABLE_REGISTRATIONS = True

AVAILABLE_LANGUAGES = ('nl', 'de', 'fr')
