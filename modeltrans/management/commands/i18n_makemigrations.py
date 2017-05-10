from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Creates the datamigration the specified app'

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='+', type=str)

    def handle(self, *args, **options):
        from modeltrans.migration import get_translatable_models

        models = get_translatable_models()

        apps = defaultdict(list)
        for model in models:
            apps[model._meta.app_label].append(model)

        for app in options['apps']:
            for model in apps[app]:
                print 'create data migration for {}'.format(model)

        # for app in options['apps']:


        # raise CommandError('App {} is not registered for translation'.format(options))
        # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
