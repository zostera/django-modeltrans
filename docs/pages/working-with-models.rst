Working with models recipes.
============================

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
