from django.db import connection


class CreateTestModel():
    '''
    Create the database table for a Model during tests.

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
    def __init__(self, Model):
        self.Model = Model

    def __enter__(self):
        '''
        Create the table in our database
        '''
        with connection.schema_editor() as editor:
            editor.create_model(self.Model)

    def __exit__(self, *args):
        '''
        Remove the table from our database
        '''
        with connection.schema_editor() as editor:
            editor.delete_model(self.Model)
