Advanced usage
==============

.. _custom_fallback:

Custom fallback language
------------------------

By default, fallback is centrally configured with :ref:`settings_fallback`.
That might not be sufficient, for example if part of the content is created for a single language which is not ``LANGUAGE_CODE``.

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
 - the original field _always_ contains the language as configured by ``LANGUAGE_CODE``.

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
