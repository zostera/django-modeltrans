from django.core.exceptions import FieldError
from django.db import models
from django.db.models import CharField, TextField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Cast, Coalesce


def get_translatable_fields_for_model(model):
    from modeltranslation2.translator import NotRegistered, translator
    try:
        return translator.get_options_for_model(model).get_field_names()
    except NotRegistered:
        return None


def is_valid_translated_field(model, field):
    if '_' not in field:
        return
    original_field = field[0:field.rfind('_')]
    return original_field in get_translatable_fields_for_model(model)


def transform_translatable_fields(model, fields):
    i18n = fields['i18n'] if 'i18n' in fields else {}
    for field, value in fields.items():
        if is_valid_translated_field(model, field):
            i18n[field] = value
            del fields[field]

    fields['i18n'] = i18n
    return fields


class MultilingualQuerySet(models.query.QuerySet):
    def get_translatable_fields(self):
        return get_translatable_fields_for_model(self.model)

    def add_i18n_annotation(self, original_field, field_name, fallback=True):
        '''
        Add an annotation to the query to extract the translated verion of a field
        from the jsonb field to allow filtering and ordering.

        Arguments:
            original_field (str): name of the original, untranslated field.
            field_name (str): name of the translated field to add the
                annotation for. For example `title_nl` will result in adding
                someting like `i18n->>title_nl AS title_nl` to the Query.
            fallback (bool): If `True`, `COALESCE` will be used to get the value
                of the original field if the requested translation is not
                available.
        '''
        assert field_name.startswith(original_field)

        if original_field not in self.get_translatable_fields():
            raise FieldError('Field ({}) is not defined as translatable'.format(original_field))

        if fallback:
            # fallback to the original untranslated field
            field = Coalesce(RawSQL('i18n->>%s', (field_name, )), original_field, output_field=CharField())
        else:
            field = Cast(RawSQL('i18n->>%s', (field_name, )), TextField())

        self.query.add_annotation(field, field_name)

    def create(self, **kwargs):
        '''
        Patch the create method to allow adding the value for a translated field
        using `Model.objects.create(..., title_nl='...')`.
        '''
        return super(MultilingualQuerySet, self).create(
            **transform_translatable_fields(self.model, kwargs)
        )

    def order_by(self, *field_names):
        '''
        Annotate translated fields before sorting
        sorting on `-title_nl` will add an annotation for `title_nl`
        '''

        for field in field_names:
            if '_' not in field:
                continue

            # remove descending prefix, not relevant for the annotation
            if field[0] == '-':
                field = field[1:]

            original_field = field[0:field.rfind('_')]

            self.add_i18n_annotation(original_field, field, fallback=True)

        return super(MultilingualQuerySet, self).order_by(*field_names)

    def _filter_or_exclude(self, negate, *args, **kwargs):
        '''
        Annotate filter/exclude fields before filtering.

        title_nl__contains='foo' should add an annotation for title_nl
        title_nl='bar' should add an annotation for title_nl
        '''
        for field in kwargs.keys():
            for translatable in self.get_translatable_fields():
                # strip the query type
                if '__' in field:
                    field = field[0:field.rfind('__')]

                if field.startswith(translatable) and '_' in field:
                    original_field = field[0:field.rfind('_')]
                    self.add_i18n_annotation(original_field, field, fallback=False)

        # TODO: handle args to translate the Q objects

        return super(MultilingualQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)


def multilingual_queryset_factory(old_cls, instantiate=True):
    '''Return a MultilingualQuerySet, or mix MultilingualQuerySet in custom QuerySets.'''
    if old_cls == models.query.QuerySet:
        NewClass = MultilingualQuerySet
    else:
        class NewClass(old_cls, MultilingualQuerySet):
            pass
        NewClass.__name__ = 'Multilingual%s' % old_cls.__name__
    return NewClass() if instantiate else NewClass


class MultilingualQuerysetManager(models.Manager):
    def get_queryset(self):
        qs = super(MultilingualQuerysetManager, self).get_queryset()
        return self._patch_queryset(qs)

    def _patch_queryset(self, qs):
        qs.__class__ = multilingual_queryset_factory(qs.__class__, instantiate=False)
        return qs


class MultilingualManager(MultilingualQuerysetManager):
    use_for_related_fields = True

    def rewrite(self, *args, **kwargs):
        return self.get_queryset().rewrite(*args, **kwargs)

    def populate(self, *args, **kwargs):
        return self.get_queryset().populate(*args, **kwargs)

    def raw_values(self, *args, **kwargs):
        return self.get_queryset().raw_values(*args, **kwargs)

    def get_queryset(self):
        '''
        This method is repeated because some managers that don't use super() or alter queryset class
        may return queryset that is not subclass of MultilingualQuerySet.
        '''
        qs = super(MultilingualManager, self).get_queryset()
        if isinstance(qs, MultilingualQuerySet):
            # Is already patched by MultilingualQuerysetManager - in most of the cases
            # when custom managers use super() properly in get_queryset.
            return qs
        return self._patch_queryset(qs)

    get_query_set = get_queryset
