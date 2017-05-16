# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
from collections import defaultdict

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates the datamigration the specified app'

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='+', type=str)

    def handle(self, *args, **options):
        from modeltrans.migration import (get_translatable_models,
                                          I18nMigration, get_translated_fields, get_latest_migration)

        models = get_translatable_models()

        apps = defaultdict(list)
        for model in models:
            apps[model._meta.app_label].append(model)

        for app in options['apps']:
            print('Create migration for app:', app)

            if len(apps[app]) == 0:
                print('No models registered for translation with django-modeltranslation')
                return
            migration = I18nMigration(app)

            for Model in apps[app]:
                translatable_fields = tuple(get_translated_fields(Model))

                print('added model "{}" with fields [{}]('.format(
                    Model.__name__,
                    str(translatable_fields)
                ))
                migration.add_model(Model, translatable_fields)

            output = get_latest_migration(app)
            output = '{0:04d}_i18n_data_migration.py'.format(int(output[0:4]) + 1)
            print('Writing to migration to {}'.format(output))

            from django.conf import settings
            # TODO: fix this path:
            path = os.path.join(settings.BASE_DIR, 'migrate_test', app, 'migrations')
            with open(os.path.join(path, output), 'w') as f:
                migration.write(f)
