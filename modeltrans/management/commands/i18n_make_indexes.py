# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.core.management.base import BaseCommand

from modeltrans.translator import get_translated_models


class Command(BaseCommand):
    help = 'Creates the i18n GIN indexes for the specified app'

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='+', type=str)

    def handle(self, *args, **options):
        from modeltrans.migration import I18nIndexMigration

        for app in options['apps']:
            print('Create migration to add GIN indexes for app:', app)
            models = list(get_translated_models(app))

            if len(models) == 0:
                print('No models in this app have a i18n = TranslationField()')
                break
            migration = I18nIndexMigration(app)

            for Model in models:
                print('added model "{}".'.format(Model.__name__))
                migration.add_model(Model, ())

            filename = migration.write_migration_file()
            print('Wrote migration for {} to {}'.format(app, filename))
