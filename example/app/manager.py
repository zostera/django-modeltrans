from django.db import models
from django.db.models import CharField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce


def get_translatable_fields_for_model(model):
    return getattr(model, 'translatable', None)


class MultilingualQuerySet(models.query.QuerySet):
    def _post_init(self):
        return

    def _rewrite_applied_operations(self):
        return

    def order_by(self, *field_names):
        '''Annotate the queryset if a translated field is requested for sorting'''
        translatable = get_translatable_fields_for_model(self.model)

        for field in field_names:
            # remove descending prefix to create the annotation
            if field[0] == '-':
                field = field[1:]

            if '_' in field:
                base = field.split('_')[0]  # todo, split on last _, not on first

                if base in translatable:
                    # annotate query, with fallback on original field
                    self.query.add_annotation(
                        Coalesce(RawSQL('i18n->>%s', (field, )), base, output_field=CharField()),
                        field
                    )

        return super(MultilingualQuerySet, self).order_by(*field_names)


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
        qs._post_init()
        qs._rewrite_applied_operations()
        return qs
