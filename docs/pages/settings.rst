Settings Reference
==================

django-modeltrans needs some settings to define it's behaviour. By default, it tries to
use sensible defaults derived from the default django settings.

``MODELTRANS_AVAILABLE_LANGUAGES``
----------------------------------
A list of language codes to allow model fields to be translated in. By default,
the language codes extracted from django's `LANGUAGES setting <https://docs.djangoproject.com/en/stable/ref/settings/#languages>`_.

Note that
 - the default language, defined in django's `LANGUAGE_CODE setting <https://docs.djangoproject.com/en/stable/ref/settings/#language-code>`_,
   should not be added to this list.
 - order is not important

A custom definition might be::

    MODELTRANS_AVAILABLE_LANGUAGES = ('en', 'de', 'fr')
