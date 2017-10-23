
try:
    from django.contrib.postgres.fields.jsonb import KeyTextTransform
except ImportError:
    # django 1.11 implementation of KeyTextTransform for django 1.10 and 1.9
    from django.contrib.postgres.fields.jsonb import KeyTransform
    from django.db.models import TextField

    class KeyTextTransform(KeyTransform):
        operator = '->>'
        nested_operator = '#>>'
        _output_field = TextField()
