# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from collections import defaultdict

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates the i18n GIN indexes for the specified app'

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='+', type=str)

    def handle(self, *args, **options):
        from modeltrans.migration import (I18nIndexMigration, get_next_migration_filename, get_translatable_models,
                                          get_translated_fields)

        models = get_translatable_models()

        apps = defaultdict(list)
        for model in models:
            apps[model._meta.app_label].append(model)

        for app in options['apps']:
            print('Create migration to add GIN indexes for app:', app)

            if len(apps[app]) == 0:
                print('No models in this app have a i18n = TranslationField()')
                break
            migration = I18nIndexMigration(app)

            for Model in apps[app]:
                translatable_fields = tuple(get_translated_fields(Model))

                print('added model "{}".'.format(Model.__name__))
                migration.add_model(Model, translatable_fields)

            filename = migration.write_migration_file()
            print('Wrote migration for {} to {}'.format(app, filename))
