# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import inspect
import os
import sys

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader
from django.utils.timezone import now

from . import __version__ as VERSION
from .conf import get_default_language
from .utils import split_translated_fieldname

try:
    from modeltranslation.translator import translator
    DJANGO_MODELTRANSLATION_AVAILABLE = True
except ImportError:
    DJANGO_MODELTRANSLATION_AVAILABLE = False

DEFAULT_LANGUAGE = get_default_language()


def _raise_if_not_django_modeltranslation():
    '''Raise if we cannot import django-modeltranslation during migration'''
    if not DJANGO_MODELTRANSLATION_AVAILABLE:
        raise ImproperlyConfigured(
            'django-modeltranslation must be still installed when creating'
            'the modeltranslation -> modeltrans migrations.'
        )


def get_translatable_models():
    '''
    Get the translatable models according to django-modeltranslation

    !! only use to migrate from django-modeltranslation !!
    '''
    _raise_if_not_django_modeltranslation()
    return translator.get_registered_models()


def get_translated_fields(Model):
    '''
    Enumerates the translated fields for a model according to django-modeltranslation.
    For example: title_nl, title_en, title_fr, body_nl, body_en, body_fr

    !! only use to migrate from django-modeltranslation !!
    '''
    _raise_if_not_django_modeltranslation()

    options = translator.get_options_for_model(Model)
    for original_field, fields in options.fields.items():
        for translated in fields:
            yield translated.name


def copy_translations(Model, fields):
    '''
    Copy translations for all items in the database for a Model with
    translations managed by django-modeltranslation into a json field `i18n`
    managed by django-modeltrans.
    Values for the default language will be copied to the original field.

    Arguments:
        Model: A (historical) Model from the migraton's app registry
        fields(iterable): list of fields to copy into their new places.
    '''
    for m in Model.objects.all():
        m.i18n = {}
        for field in fields:
            value = getattr(m, field)
            if value is None:
                continue

            original_field, lang = split_translated_fieldname(field)

            if lang == DEFAULT_LANGUAGE:
                setattr(m, original_field, value)
            else:
                m.i18n[field] = value

        m.save()


def get_latest_migration(app_name, connection=None):
    '''
    Get the name of the latest applied migration and raises if unapplied
    migrations exist for the app.

    Arguments:
        app_name(str): Name of the app.
        connection: database connection to get the latest migration for.
    Simplified version of
    https://github.com/django/django/blob/1.9.2/django/core/management/commands/showmigrations.py#L38-L77
    '''
    if connection is None:
        connection = connections[DEFAULT_DB_ALIAS]

    loader = MigrationLoader(connection, ignore_no_migrations=True)
    graph = loader.graph
    last = None
    shown = set()
    for node in graph.leaf_nodes(app_name):
        for plan_node in graph.forwards_plan(node):
            if plan_node not in shown and plan_node[0] == app_name:
                if plan_node in loader.applied_migrations:
                    last = plan_node[1]
                else:
                    raise Exception('You have unapplied migration(s) for app {}'.format(app_name))
                shown.add(plan_node)

    return last


def get_next_migration_filename(app_name, connection=None):
    '''
    Return name (including the absolute path) of the next migration to insert for this app
    '''
    latest_migration_name = get_latest_migration(app_name)
    next_migration_name = '{0:04d}_i18n_data_migration.py'.format(int(latest_migration_name[0:4]) + 1)
    app_path = os.path.join(*apps.get_app_config(app_name).name.split('.'))

    return os.path.join(settings.BASE_DIR, app_path, 'migrations', next_migration_name)


class I18nMigration(object):
    helper_functions = (
        split_translated_fieldname,
        copy_translations,
    )

    def __init__(self, app):
        self.models = []
        self.app = app

        self.migration_filename = get_latest_migration(self.app) or '# TODO: manually insert latest migration here'

    def get_helper_functions(self):
        for fn in self.helper_functions:
            yield inspect.getsource(fn)

    def add_model(self, Model, fields):
        self.models.append(
            (Model, fields)
        )

    def write(self, out=None):
        if out is None:
            out = sys.stdout

        indexes = '\n'.join(
            [CREATE_INDEX_TEMPLATE.format(table=Model._meta.db_table) for Model, fields in self.models]
        )

        out.write(MIGRATION_TEMPLATE.format(
            version=VERSION,
            DEFAULT_LANGUAGE=getattr(settings, 'MODELTRANSLATION_DEFAULT_LANGUAGE', get_default_language()),
            timestamp=now().strftime('%Y-%m-%d %H:%M'),
            helpers='\n\n'.join(self.get_helper_functions()),
            todo=',\n        '.join([str((Model.__name__, fields)) for Model, fields in self.models]),
            app=self.app,
            last_migration=self.migration_filename,
            indexes=indexes
        ))


CREATE_INDEX_TEMPLATE = '''
        migrations.RunSQL(
            [("CREATE INDEX IF NOT EXISTS {table}_i18n_gin ON {table} USING gin (i18n jsonb_path_ops);", None)],
            [('DROP INDEX {table}_i18n_gin;', None)],
        ),'''

MIGRATION_TEMPLATE = '''
# -*- coding: utf-8 -*-
# Generated by django-modeltrans {version} on {timestamp}

from __future__ import print_function, unicode_literals

from django.db import migrations

DEFAULT_LANGUAGE = '{DEFAULT_LANGUAGE}'


{helpers}

def forwards(apps, schema_editor):
    app = '{app}'
    todo = (
        {todo},
    )

    for model, fields in todo:
        Model = apps.get_model(app, model)

        copy_translations(Model, fields)


class Migration(migrations.Migration):

    dependencies = [
        ('{app}', '{last_migration}'),
    ]

    operations = [
        # The copying of values is (sort of) reversable by a no-op:
        #  - values are copied into i18n (which is not used by anything but django-modeltrans)
        #  - the default language is copied to the orignal field, which was not used
        #    with django-modeltrans.
        migrations.RunPython(forwards, migrations.RunPython.noop),
        {indexes}
    ]
'''
