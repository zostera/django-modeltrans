from django.db import connection, models


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
    def __init__(self, *models):
        self.models = models

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
            for Model in self.models:
                editor.delete_model(Model)
