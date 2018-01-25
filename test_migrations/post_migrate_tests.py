from django.db import connection
from django.test import TestCase
from django.utils.translation import override

from migrate_test.app.models import Blog


def get_indexes(table):
    """
    Get the type, column-name tuples for all single-column indexes on the table using a new cursor.

    Adapted from
    from django/django django/tests/schema/tests.py::SchemaTests
    https://github.com/django/django/blob/6afede82192067efecedb039c29eb301816d5fb5/tests/schema/tests.py#L112
    """
    with connection.cursor() as cursor:
        return [
            (c['type'], c['columns'][0])
            for c in connection.introspection.get_constraints(cursor, table).values()
            if c['index'] and len(c['columns']) == 1
        ]


class PostMigrateTest(TestCase):
    def test_verify_installed_apps(self):
        from django.conf import settings

        self.assertIn('modeltrans', settings.INSTALLED_APPS)
        self.assertNotIn('modeltranslation', settings.INSTALLED_APPS)

    def test_model_fields(self):
        falcon = Blog.objects.get(title='Falcon')
        self.assertEquals(falcon.i18n['title_nl'], 'Valk')
        self.assertEquals(falcon.i18n['title_de'], 'Falk')
        self.assertIn('body_nl', falcon.i18n)

        with override('nl'):
            self.assertEquals(falcon.title_i18n, 'Valk')

        with override('de'):
            self.assertEquals(falcon.title_i18n, 'Falk')

    def test_indexes_in_place(self):
        '''
        Check if the i18n column has the gin index.
        '''
        db_table = Blog._meta.db_table
        indexes = get_indexes(db_table)

        self.assertIn(('gin', 'i18n'), indexes)
