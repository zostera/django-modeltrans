from django.db.models import Transform
from django.db.models.fields import Field
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models import (
    Field, TextField, Transform, lookups as builtin_lookups
)


class I18nTransform(KeyTextTransform):
    lookup_name = 'i18n'

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


@Field.register_lookup
class I18nTransformIExact(I18I18nTransform, builtin_lookups.IExact):
    pass
