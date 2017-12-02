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
