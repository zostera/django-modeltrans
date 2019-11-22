from io import StringIO

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase

from modeltrans.fields import TranslationField
from modeltrans.migration import I18nDataMigration, copy_translations, get_translatable_models

from .app.models import Blog, Category
from .utils import CreateTestModel


def get_output(migration):
    output = StringIO()
    migration.write(output)
    return output.getvalue()


class I18nMigrationsTest(TestCase):
    def test_I18nDataMigration(self):
        m = I18nDataMigration("test_app")
        m.add_model(Blog, ("title_nl", "title_fr", "body_nl", "body_fr"))
        m.add_model(Category, ("name_nl", "name_fr"))

        output = get_output(m)
        self.assertTrue("Blog" in output)
        self.assertTrue("title_nl" in output)
        self.assertTrue("title_fr" in output)
        self.assertTrue("migrations.RunPython(forwards, migrations.RunPython.noop)" in output)

    def test_get_translatable_models(self):
        """
        get_translatable_models() Should only work if django-modeltranslation is
        available.
        So if this test fails in your dev environment, you probably have
        django-modeltranslation installed
        """

        with self.assertRaises(ImproperlyConfigured):
            get_translatable_models()

    def test_copy_translations(self):
        """
        This model looks like the state in which copy_translations is called during the data migration
        """

        class TestModel(models.Model):
            title = models.CharField(max_length=255)
            title_en = models.CharField(max_length=255)
            title_nl = models.CharField(max_length=255)
            title_de = models.CharField(max_length=255)

            body = models.TextField(null=True)
            body_en = models.TextField(null=True)
            body_nl = models.TextField(null=True)

            i18n = TranslationField(fields=("title", "body"), virtual_fields=False)

            class Meta:
                app_label = "tests"

        with CreateTestModel(TestModel):
            m = TestModel.objects.create(
                title="Falcon-gibberish", title_en="Falcon", title_nl="Valk"
            )

            copy_translations(TestModel, ("title_en", "title_nl", "body_en", "body_nl"))

            m.refresh_from_db()
            self.assertEqual(m.title_en, "Falcon")
            self.assertEqual(m.i18n, {"title_nl": "Valk"})

            m = TestModel.objects.create(title_en="Falcon", title_nl="Valk", title_de="")
            copy_translations(TestModel, ("title_en", "title_nl", "title_de"))
            m.refresh_from_db()
            self.assertEqual(m.i18n, {"title_nl": "Valk"})
