from django.test import TestCase
from django.utils.translation import override

from migrate_test.app.models import Blog


class PreMigrateTest(TestCase):
    def test_verify_installed_apps(self):
        from django.conf import settings

        self.assertNotIn('modeltrans', settings.INSTALLED_APPS)
        self.assertIn('modeltranslation', settings.INSTALLED_APPS)

    def test_model_fields(self):
        self.assertEquals(
            {field.name for field in Blog._meta.get_fields()},
            {
                'id',
                'title', 'title_de', 'title_en', 'title_fr', 'title_nl',
                'body', 'body_de', 'body_en', 'body_fr', 'body_nl',
                'category'
            }
        )

    def test_data_available(self):
        def get_titles():
            return {m.title for m in Blog.objects.all()}

        self.assertEquals(get_titles(), {'Falcon', 'Dolphin', 'Vulture'})

        with override('de'):
            self.assertEquals(get_titles(), {'Falk', 'Delfin', ''})
