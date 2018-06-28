import json
import os

from django.db import connection

from .app.models import Blog, Category


class CreateTestModel:
    """
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
    """

    def __init__(self, *args):
        self.models = args

    def __enter__(self):
        """
        Create the tables in our database
        """
        with connection.schema_editor() as editor:
            for Model in self.models:
                editor.create_model(Model)

    def __exit__(self, *args):
        """
        Remove the tables from our database
        """
        with connection.schema_editor() as editor:
            for Model in reversed(self.models):
                editor.delete_model(Model)


def load_wiki():
    wiki = Category.objects.create(name="Wikipedia")
    with open(os.path.join("tests", "fixtures", "fulltextsearch.json")) as infile:
        data = json.load(infile)

        for article in data:
            kwargs = {}
            for item in article:
                lang = "_" + item["lang"]

                kwargs["title" + lang] = item["title"]
                kwargs["body" + lang] = item["body"]

            Blog.objects.create(category=wiki, **kwargs)
