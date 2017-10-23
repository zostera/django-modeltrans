
try:
    from django.contrib.postgres.fields.jsonb import KeyTextTransform
except ImportError:
    from django.contrib.postgres.fields.jsonb import Transform
    from django.db.models import TextField

    # django 1.11 implementation of KeyTextTransform for django 1.10 and 1.9
    # remove when support for django 1.9 and 1.0 is dropped

    class KeyTransform(Transform):
        operator = '->'
        nested_operator = '#>'

        def __init__(self, key_name, *args, **kwargs):
            super(KeyTransform, self).__init__(*args, **kwargs)
            self.key_name = key_name

        def as_sql(self, compiler, connection):
            key_transforms = [self.key_name]
            previous = self.lhs
            while isinstance(previous, KeyTransform):
                key_transforms.insert(0, previous.key_name)
                previous = previous.lhs
            lhs, params = compiler.compile(previous)
            if len(key_transforms) > 1:
                return "(%s %s %%s)" % (lhs, self.nested_operator), [key_transforms] + params
            try:
                int(self.key_name)
            except ValueError:
                lookup = "'%s'" % self.key_name
            else:
                lookup = "%s" % self.key_name
            return "(%s %s %s)" % (lhs, self.operator, lookup), params

    class KeyTextTransform(KeyTransform):
        operator = '->>'
        nested_operator = '#>>'
        _output_field = TextField()
