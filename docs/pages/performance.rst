Database performance
====================

Adding gin indexes
++++++++++++++++++

In order to perform well while performing filtering or ordering on translated values,
the ``i18n``-field need a GIN index.
An index is added automatically while migrating from django-modeltranslation,
but has to be added manually if not.
