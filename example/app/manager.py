from django.core.exceptions import FieldError
from django.db import models
from django.db.models import CharField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Cast, Coalesce


class MultilingualQuerySet(models.query.QuerySet):
    def get_translatable_fields(self):
        return getattr(self.model, 'translatable', None)

    def add_i18n_annotate(self, field_name, fallback=True):
        '''
        Add an annotation to the query to extract the translated verion of a field
        from the jsonb field to allow filtering and ordering
        '''
        if '_' not in field_name:
            return
            # raise FieldError('Cannot extract a field ({}), it does not contain a language designator'.format(field_name))

        # TODO: split on last _, not on first
        original = field_name.split('_')[0]

        if original in self.get_translatable_fields():
            if fallback:
                # fallback to the original untranslated field
                field = Coalesce(RawSQL('i18n->>%s', (field_name, )), original, output_field=CharField())
            else:
                field = Cast(RawSQL('i18n->>%s', (field, )), CharField())

            self.query.add_annotation(field, field_name)

    def order_by(self, *field_names):
        '''Annotate the queryset if a translated field is requested for sorting'''

        for field in field_names:
            # remove descending prefix to create the annotation
            if field[0] == '-':
                field = field[1:]
            self.add_i18n_annotate(field)

        return super(MultilingualQuerySet, self).order_by(*field_names)

    def filter(self, *args, **kwargs):
        return super(MultilingualQuerySet, self).filter(*args, **kwargs)


def multilingual_queryset_factory(old_cls, instantiate=True):
    '''Return a MultilingualQuerySet, or mix MultilingualQuerySet in custom QuerySets.'''
    if old_cls == models.query.QuerySet:
        NewClass = MultilingualQuerySet
    else:
        class NewClass(old_cls, MultilingualQuerySet):
            pass
        NewClass.__name__ = 'Multilingual%s' % old_cls.__name__
    return NewClass() if instantiate else NewClass


class MultilingualQuerySetManager(models.Manager):
    def get_queryset(self):
        qs = super(MultilingualQuerySetManager, self).get_queryset()
        return self._patch_queryset(qs)

    def _patch_queryset(self, qs):
        qs.__class__ = multilingual_queryset_factory(qs.__class__, instantiate=False)
        # qs._post_init()
        # qs._rewrite_applied_operations()
        return qs
