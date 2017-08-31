Migrating from django-modeltranslation
======================================

This is how to migrate from django-modeltranslation (version 0.12.1) to
`django-modeltrans`:

#. Make sure you have a recent backup of your data available!
#. Add `modeltrans` to your `INSTALLED_APPS`
#. Make sure the default language for django-modeltranslation is equal to the
   language in `LANGUAGE_CODE`, which django-modeltrans will use.
#. Copy the setting `AVAILABLE_LANGUAGES` to `MODELTRANS_AVAILABLE_LANAGUES`.
#. Add the TranslationField to the models you want to translate and keep the registrations
   for now. In order to prevent field name collisions, disable the virtual fields in django-modeltrans
   for now (`virtual_fields=False`)::

    # models.py
    from django.db import models
    from modeltrans.fields import TranslationField

    class Blog(models.Model):
        title = models.CharField(max_length=255)
        body = models.TextField(null=True)

        # add this field, containing the TranslationOptions attributes as arguments:
        i18n = TranslationField(fields=('title', 'body'), virtual_fields=False)


    # translation.py
    from modeltranslation.translator import translator, TranslationOptions
    from .models import Blog

    class BlogTranslationOptions(TranslationOptions):
        fields = ('name', 'title', )

    translator.register(Blog, BlogTranslationOptions)

#. Run `./manage.py makemigrations <apps>`. This will create the
   migration adding the `i18n`-fields required by django-modeltrans. Apply
   them with `./manage.py migrate`
#. We need to create a migration to copy the values of the translated
   fields into the newly created `i18n`-field. django-modeltrans provides
   a management command to do that `./manage.py i18n_makemigrations <apps>`
#. Now, remove django-modeltranslation by:
   - Remove `modeltranslation` from `INSTALLED_APPS`.
   - Remove django-modeltranslation settings (`DEFAULT_LANGUAGE`, `AVAILABLE_LANGUAGES`) from your `settings.py`'s
   - Remove all `translation.py` files from your apps.
   - Remove the use of `modeltranslation.admin.TranslationAdmin` in your `admin.py`'s

#. Run `./manage.py makemigrations <apps>`. This will remove the translated
   fields from your registered models.
#. Update your code: use  the `<field>_i18n` field in places where you would use `<field>`
   with django-modeltranslation. Less magic, but
   `explicit is better than implicit <https://www.python.org/dev/peps/pep-0020/>`_!
