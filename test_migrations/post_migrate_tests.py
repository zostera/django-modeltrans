from django.test import TestCase
from django.utils.translation import override

from migrate_test.app.models import Blog


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
