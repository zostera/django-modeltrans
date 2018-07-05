Database performance
====================

Adding GIN indexes
++++++++++++++++++

In order to perform well while filtering or ordering on translated values,
the ``i18n``-field need a GIN index. Due to limitations in the way Django currently
allows to define indexes, they should be added manually::

    from django.contrib.postgres.indexes import GinIndex
    from django.db import models


    class Category(models.Model):
        name = models.CharField(max_length=255)

        i18n = TranslationField(fields=("name",))

        class Meta:
            indexes = [GinIndex(fields=["i18n"]]
