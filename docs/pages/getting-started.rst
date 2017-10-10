Getting started
===============

 - Add ``'modeltrans'`` your list of ``INSTALLED_APPS``.
 - Make sure the current data in your models is in the language defined in the ``LANGUAGE_CODE`` django setting.
 - By default, django-modeltrans uses the languages in the ``LANGUAGES`` django setting. If you want
   the list to be different, add a list of available languages to your ``settings.py``:
   ``MODELTRANS_AVAILABLE_LANGUAGES = ('en', 'nl', 'de', 'fr')``.
 - Add a ``modeltrans.fields.TranslationField`` to your models and specify the fields you
   want to translate::

    # models.py
    from django.db import models
    from modeltrans.fields import TranslationField


    class Blog(models.Model):
        title = models.CharField(max_length=255)
        body = models.TextField(null=True)

        i18n = TranslationField(fields=('title', 'body'))

 - Run ``./manage.py makemigrations`` to add the ``i18n`` JSONField to each model containing
   translations.
 - Each Model now has some extra virtual fields. In the example above:

   - ``title`` allows getting/setting the default language
   - ``title_nl``, ``title_de``, ... allow getting/setting the specific languages
   - If ``LANGUAGE_CODE == 'en'``, ``title_en`` is mapped to ``title``.
   - ``title_i18n`` follows the currently active translation in Django, and falls back to the default language

The above could be used in a Django shell like this::

    >>> b = Blog.objects.create(title='Falcon', title_nl='Valk')
    >>> b.title
    'Falcon'
    >>> b.title_nl
    'Valk'
    >>> b.title_i18n
    'Falcon'
    >>> from django.utils.translation import override
    >>> with override('nl'):
    ...   b.title_i18n
    ...
    'Valk'
    # translations are stored in the field ``i18n`` in each model:
    >>> b.i18n
    {u'title_nl': u'Valk'}
    # if a translation is not available, None is returned.
    >>> print(b.title_de)
    None
    # fallback to the default language
    >>> with override('de'):
    ...     b.title_i18n
    'Falcon'
    # now, if we set the German tranlation, it it is returned from title_i18n:
    >>> b.title_de = 'Falk'
    >>> with override('de'):
    ...     b.title_i18n
    'Falk'
