Settings Reference
==================

django-modeltrans allows some configuration to define it's behaviour.
By default, it tries to use sensible defaults derived from the default django settings.

``MODELTRANS_AVAILABLE_LANGUAGES``
----------------------------------
A list of language codes to allow model fields to be translated in. By default,
the language codes extracted from django's `LANGUAGES setting <https://docs.djangoproject.com/en/stable/ref/settings/#languages>`_.

Note that
 - the default language, defined in django's `LANGUAGE_CODE setting <https://docs.djangoproject.com/en/stable/ref/settings/#language-code>`_,
   should not be added to this list (will be ignored).
 - order is not important

A custom definition might be::

    MODELTRANS_AVAILABLE_LANGUAGES = ('de', 'fr')


``MODELTRANS_FALLBACK``
-----------------------
A dict of fallback chains as lists of languages. By default, it falls back to the language defined in django setting `LANGUAGE_CODE`.

For example, django-modeltrans will fall back to:
 - english when the active language is 'nl'
 - fist dutch and finally english with active language is 'fy'

If configured like this::

    LANGUAGE_CODE = 'en'
    MODELTRANS_AVAILABLE_LANGUAGES = ('nl', 'fy')
    MODELTRANS_FALLBACK = {
       'default': (LANGUAGE_CODE, ),
       'fy': ('nl', 'en')
    }


``MODELTRANS_CREATE_GIN``
-------------------------
Boolean signalling django-modeltrans to create a `GinIndex <https://docs.djangoproject.com/en/stable/ref/contrib/postgres/indexes/#ginindex>`_
for each ``i18n`` field.
Support for ``GinIndex`` is added in django 1.11, for previous versions,
use :ref:`add_gin_index`.

``True`` by default.
