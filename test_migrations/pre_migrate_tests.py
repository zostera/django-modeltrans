from django.unittest import TestCase


class PreMigrateTest(TestCase):
    fixtures = ['data.json']
