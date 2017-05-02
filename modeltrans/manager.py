# -*- coding: utf-8 -*-

from django.core.exceptions import FieldError
from django.db import models
from django.db.models import CharField, TextField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Cast, Coalesce

from . import settings


def get_translatable_fields_for_model(model):
    from modeltrans.translator import NotRegistered, translator
    try:
        return translator.get_options_for_model(model).get_field_names()
    except NotRegistered:
        return None


def split_translated_fieldname(field_name):
    _pos = field_name.rfind('_')
    return (field_name[0:_pos], field_name[_pos + 1:])


def is_valid_translated_field(model, field):
    if '_' not in field:
        return
    original_field, lang = split_translated_fieldname(field)
    return original_field in get_translatable_fields_for_model(model)


def transform_translatable_fields(model, fields):
    '''
    Transform the kwargs for a <Model>.objects.create() or <Model>()
    to allow passing translated field names.
    '''
    ret = {
        'i18n': fields.get('i18n', {})
    }

    for field, value in fields.items():
        original_field, lang = split_translated_fieldname(field)

        if lang == settings.DEFAULT_LANGUAGE:
            ret[original_field] = value
        elif original_field in get_translatable_fields_for_model(model):
            ret['i18n'][field] = value
        else:
            ret[field] = value

    return ret


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

            _pos = field.rfind('_')
            original_field = field[0:_pos]
            #
            # lang = field[_pos:]
            # if lang == 'i18n':
            #     # add annotation for current language.
            #     lang = get_language()
            #     if lang == DEFAULT_LANGUAGE:
            #

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


class MultilingualManager(models.Manager):
    use_for_related_fields = True

    def _patch_queryset(self, qs):
        qs.__class__ = multilingual_queryset_factory(qs.__class__, instantiate=False)
        return qs

    def get_queryset(self):
        '''
        This method is repeated because some managers that don't use super() or alter queryset class
        may return queryset that is not subclass of MultilingualQuerySet.
        '''
        qs = super(MultilingualManager, self).get_queryset()
        if isinstance(qs, MultilingualQuerySet):
            # Is already patched
            return qs
        return self._patch_queryset(qs)
