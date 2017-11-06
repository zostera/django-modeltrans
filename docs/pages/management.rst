.. _management_commands:

Management commands
===================

The packages adds a management command to create relevant migrations
not automatically created by the ``./manage.py makemigrations`` command.


Data migration to migrate from django-modeltranslation
------------------------------------------------------

Syntax: ``./manage.py i18n_makemigrations <apps>``

Only to migrate data from the fields managed by django-modeltranslation to
the JSON field managed by django-modeltrans.

Explained in more detail in :ref:`modeltranslation_migration`


.. _add_gin_index:

Adding GIN indexes to the JSON field
------------------------------------

Syntax: ``./manage.py i18n_make_indexes <apps>``

In Django 1.11 and later, a GIN index is automatically added with the
``i18n``-field. For 1.9 and 1.10 you can use this command.
