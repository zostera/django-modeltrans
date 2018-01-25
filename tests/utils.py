import json
import os

from django.db import connection

from .app.models import Blog, Category


class CreateTestModel():
    '''
    Create the database table for a one or more Models during tests.

    Helpfull if we want to use custom settings which influence the models
    created in our tests, used like this::

        class Test(TestCase):

            @override_settings(LANGUAGE_CODE='nl')
            def test_with_custom_model(self):
                class TestModel(models.Model):
                    title = models.CharField(max_length=10)

                with CreateTestModel(TestModel):
                    m = TestModel.objects.create(title='foo')

                    self.assertEquals(m.title, 'foo')
    '''
    def __init__(self, *args):
        self.models = args

    def __enter__(self):
        '''
        Create the tables in our database
        '''
        with connection.schema_editor() as editor:
            for Model in self.models:
                editor.create_model(Model)

    def __exit__(self, *args):
        '''
        Remove the tables from our database
        '''
        with connection.schema_editor() as editor:
            for Model in reversed(self.models):
                editor.delete_model(Model)


def load_wiki():
    wiki = Category.objects.create(name='Wikipedia')
    with open(os.path.join('tests', 'fixtures', 'fulltextsearch.json')) as infile:
        data = json.load(infile)

        for article in data:
            kwargs = {}
            for item in article:
                lang = '_' + item['lang']

                kwargs['title' + lang] = item['title']
                kwargs['body' + lang] = item['body']

            Blog.objects.create(category=wiki, **kwargs)


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
