Advanced usage
==============

.. _custom_fallback:

Custom fallback language
------------------------

By default, fallback is centrally configured with :ref:`settings_fallback`.
That might not be sufficient, for example if part of the content is created for a single language which is not ``MODELTRANS_DEFAULT_LANGUAGE``.

In that case, it can be configured per-record using the ``fallback_language_field`` argument to ``TranslationField``::

    class NewsRoom(models.Model):
        name = models.CharField(max_length=255)
        default_language = models.CharField(max_length=2)

        i18n = TranslationField(fields=("name",), fallback_language_field="default_language")

You can traverse foreign key relations too::

    class Article(models.Model):
        content = models.CharField(max_length=255)
        newsroom = models.ForeignKey(NewsRoom)

        i18n = TranslationField(fields=("content",), fallback_language_field="newsroom__default_language")

Note that
 - if in this example no `newsroom` is set yet, the centrally configured fallback is used.
 - the original field _always_ contains the language as configured by ``MODELTRANS_DEFAULT_LANGUAGE``.

With the models above::

    nos = NewsRoom.objects.create(name="NOS (en)", default_language="nl", name_nl="NOS (nl)")
    article = Article.objects.create(
        newsroom=nos,
        content="US-European ocean monitoring satellite launches into orbit",
        content_nl="VS-Europeese oceaanbewakingssatelliet gelanceerd"
    )

    with override('de'):
        # If language 'de' is not available, the records default_language will be used.
        print(nos.name)  # 'NOS (nl)'

        #  If language 'de' is not available, the newsroom.default_language will be used.
        print(article.content)  # 'VS-Europeese oceaanbewakingssatelliet gelanceerd'


Per-record default language
---------------------------

The value of an original field (a translatable field when used without a language suffix; for example `title`, but not
`title_nl`) is normally in the Django default language, which is the one specified by the setting `LANGUAGE_CODE`.
Translations to any other language will be stored in the model's implicitly generated JSON field. In some cases, it may
be desired to use per-record default languages instead of a single global default language. For example, for a model
for organizations from different parts of the world, each instance has a name that is in the respective local language
and it may be desired to use this local-language name by default instead of storing it in the JSON field and leaving the
original field empty for potentially many instances. Modeltrans supports this by using the argument
`default_language_field` when specifying a `TranslationField`::

    class Organization(models.Model):
        name = models.CharField(max_length=255)
        language = models.CharField(max_length=2)
        i18n = TranslationField(fields=("name",), default_language_field="language")

Now, no matter the `LANGUAGE_CODE` setting, for both of the following instances the `name` field will contain the local
name and the JSON field `i18n` will be empty::

    amsterdam = Organization.objects.create(name="Gemeente Amsterdam", language="nl")
    helsinki = Organization.objects.create(name="Helsingin kaupunki", language="fi")

In addition, the names are also available in `amsterdam.name_nl` and `helsinki.name_fi`.

The value of `default_language_field` can contain `__` to traverse foreign keys::

    class Department(models.Model):
        name = models.CharField(max_length=255)
        organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
        i18n = TranslationField(fields=("name",), default_language_field="organization__language")

Care should be taken regarding fallback. When you access the virtual field `name_i18n`, the following steps are taken to
return a value:

1. If the instance has a name in the currently active Django language, this value will be used.
2. If the model has a `fallback_language_field` and a name exists in the language stored in this field, that value will
   be used.
3. The languages in the fallback chain (as specified in the setting `MODELTRANS_FALLBACK`) will be tried and the first
   found value will be returned.
4. If no name for any of the previously tried languages exists, the value of the original field `name` will be used.

Therefore, if you specified a `default_language_field`, you should keep in mind that the fallback chain will take effect
before the original field value is returned. When using `default_language_field`, sometimes the desired behavior is to
first try to get a value in the currently active language and, if this is impossible, fall back to the per-record
default language stored in the original field instead of falling back to whatever is the global default language. To
achieve this, you have two options:

- In addition to `default_language_field="<field>"`, also specify `fallback_language_field="<field>"`.
- Set `MODELTRANS_FALLBACK["default"]` to the empty tuple `()` to disable fallback to languages other than the original
  one for all models. If you don't set `MODELTRANS_FALLBACK["default"]`, `(LANGUAGE_CODE,)` will be used, which means
  that the global default language will have precedence over the per-record default language.

**Caveat:** Changing the default language for instances cannot be easily done at the moment. When you change the default
language, you must manually move the original field values to the JSON field and the other way around. Be aware that
changing the default language of an instance may affect instances from other models as well if their
`default_language_field` refers to the changed instance via foreign keys (using the `__` syntax).


Inheritance of models with translated fields.
---------------------------------------------

When working with model inheritance, you might want to have different parameters to the `i18n`-field for the
parent and the child model. These parameters can be overridden using the `i18n_field_params` attribute and
on the child class::

    from django.db import models
    from modeltrans.fields import TranslationField

    class ParentModel(models.Model):
        info = models.CharField(max_length=255)

        i18n = TranslationField(fields=("info",), required_languages=("en",))


    class ChildModel(ParentModel):
        child_info = models.CharField(max_length=255)

        i18n_field_params = {
            "fields": ("info", "child_info"),
            "required_languages": ("nl",)
        }
