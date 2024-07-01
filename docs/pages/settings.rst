Settings Reference
==================

django-modeltrans allows some configuration to define its behavior.
By default, it tries to use sensible defaults derived from the default django settings.


``MODELTRANS_DEFAULT_LANGUAGE``
----------------------------------
A string representing the default language.  By default, the default language is set to
django's `LANGUAGE_CODE setting <https://docs.djangoproject.com/en/stable/ref/settings/#language-code>`_.

Customize this setting to change the default language used by django-modeltrans without impacting
Django's translation / locale middlewares.

See `#116 <https://github.com/zostera/django-modeltrans/issues/116>`_ for additional context.


``MODELTRANS_AVAILABLE_LANGUAGES``
----------------------------------
A list of language codes to allow model fields to be translated in. By default,
the language codes extracted from django's `LANGUAGES setting <https://docs.djangoproject.com/en/stable/ref/settings/#languages>`_.

Note that
 - the default language, defined in `MODELTRANS_DEFAULT_LANGUAGE` should not be added to this list (will be ignored).
 - order is not important

A custom definition might be::

    MODELTRANS_AVAILABLE_LANGUAGES = ('de', 'fr')


.. _settings_fallback:

``MODELTRANS_FALLBACK``
-----------------------
A dict of fallback chains as lists of languages. By default, it falls back to the language defined in `MODELTRANS_DEFAULT_LANGUAGE`.

For example, django-modeltrans will fall back to:
 - english when the active language is 'nl'
 - fist dutch and finally english with active language is 'fy'

If configured like this::

    MODELTRANS_DEFAULT_LANGUAGE = 'en'
    MODELTRANS_AVAILABLE_LANGUAGES = ('nl', 'fy')
    MODELTRANS_FALLBACK = {
       'default': (MODELTRANS_DEFAULT_LANGUAGE, ),
       'fy': ('nl', 'en')
    }

Note that a custom fallback language can be configured on a model instance if the `i18n` field is configured like this::

    class Model(models.Model):
        title = models.CharField(max_length=100)
        fallback_language = models.CharField(max_length=2)

        i18n = TranslationField(fields=("title",), fallback_language_field="fallback_language")

in which ``fallback_language_field`` refers to the model field that contains the language code.

This topic is explained in :ref:`custom_fallback`.


``MODELTRANS_ADD_FIELD_HELP_TEXT``
----------------------------------
If ``True``, the ``<name>_i18n`` fields with empty ``help_text``s will get a ``help_text`` like::

    current language: en

``True`` by default.
