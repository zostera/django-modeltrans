# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class RegistrationConfig(AppConfig):
    name = 'modeltrans'
    verbose_name = 'Django modeltrans using a registry.'

    def ready(self):
        from modeltrans.models import handle_translation_registrations
        handle_translation_registrations()


class MigrationConfig(AppConfig):
    '''
    This migrationconfig tries to ease the transition from django-modeltranslation
    (version 0.12.1) to django-modeltrans.

    This is how it is supposed to work:
    1. Make sure you have a recent backup available!
    2. Add `modeltrans.apps.MigrationConfig` to your `INSTALLED_APPS`
    3. Run `./manage.py makemigrations add_i18n_field`. This will create the
       migration adding the`i18n`-fields required by django-modeltrans. Run them
       with `./manage.py migrate`
    4. Now we need to create a migration to copy the values of the translated
       fields into the newly created `i18n`-field. django-modeltrans provides
       some has some utility functions to do that.

    4. Remove `modeltranslation` from your `INSTALLED_APPS`. This will remove the
       translated fields from your registered models.
    5. Update your code to work according to the API of django-modeltrans:
        - Change the imports in you `translation.py` to import from `modeltrans`
          instead of `modeltranslation`.
        - Use `<field>_i18n` field names for places where you would use `<field>`
          with django-modeltranslation

    '''
    name = 'modeltrans'
    verbose_name = 'Migration from django-modeltranslation to django-modeltrans'

    def ready(self):
        from django.conf import settings
        if 'modeltranslation' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                'In order to use this "model-migration" app config, you must '
                'have django-modeltranslation installed alongside this app config'
            )

        from modeltrans.models import handle_translation_registrations
        handle_translation_registrations(create_virtual_fields=False)
