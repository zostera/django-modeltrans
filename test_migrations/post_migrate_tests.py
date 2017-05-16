from django.test import TestCase

from migrate_test.app.models import Blog


# from django.utils.translation import override


class PostMigrateTest(TestCase):

    def test_model_fields(self):

        print('Post migrate tests')
        print Blog.objects.get(title='Falcon').i18n
        assert False
