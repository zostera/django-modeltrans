from django.db import connection
from django.test import TestCase
from django.utils.translation import override

from migrate_test.app.models import Blog


class PostMigrateTest(TestCase):
    def test_verify_installed_apps(self):
        from django.conf import settings

        self.assertIn("modeltrans", settings.INSTALLED_APPS)
        self.assertNotIn("modeltranslation", settings.INSTALLED_APPS)

    def test_model_fields(self):
        falcon = Blog.objects.get(title="Falcon")
        self.assertEquals(falcon.i18n["title_nl"], "Valk")
        self.assertEquals(falcon.i18n["title_de"], "Falk")
        self.assertIn("body_nl", falcon.i18n)

        with override("nl"):
            self.assertEquals(falcon.title_i18n, "Valk")

        with override("de"):
            self.assertEquals(falcon.title_i18n, "Falk")

    def test_indexes_in_place(self):
        """
        Check if the i18n column has the gin index.
        """
        db_table = Blog._meta.db_table
        index_prefix = "{}_i18n".format(db_table)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = %s;", [db_table]
            )
            indexes = {name: definition for name, definition in cursor.fetchall()}

        for name, definition in indexes.items():
            if name.startswith(index_prefix):
                self.assertIn("_gin", name)
                self.assertIn("USING gin", definition)
