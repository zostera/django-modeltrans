# -*- coding: utf-8 -*-

from django.core.exceptions import FieldError
from django.db import models
from django.db.models import TextField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Cast, Coalesce

from . import settings
from .utils import (build_localized_fieldname, get_language,
                    split_translated_fieldname)


def get_translatable_fields_for_model(Model):
    from modeltrans.translator import NotRegistered, translator
    try:
        return translator.get_options_for_model(Model).get_field_names()
    except NotRegistered:
        return None


def transform_translatable_fields(model, fields):
    '''
    Transform the kwargs for a <Model>.objects.create() or <Model>()
    to allow passing translated field names.

    Arguments:
        fields (dict): kwargs to a model __init__ or Model.objects.create() method
            for which the field names need to be translated to values in the i18n field
    '''

    ret = {
        'i18n': fields.get('i18n', {})
    }

    for field, value in fields.items():
        original_field, lang = split_translated_fieldname(field)

        if lang == settings.DEFAULT_LANGUAGE:
            if original_field in fields:
                raise ValueError(
                    'Attempted override of "{}" with "{}". '
                    'Only one of the two is allowed.'.format(original_field, field)
                )
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
        Add an annotation to the query to extract the translated version of a field
        from the jsonb field to allow filtering and ordering.

        Arguments:
            original_field (str): name of the original, untranslated field.
            field_name (str): name of the translated field to add the
                annotation for. For example `title_nl` will result in adding
                something like `i18n->>title_nl AS title_nl_annotation` to the Query.
            fallback (bool): If `True`, `COALESCE` will be used to get the value
                of the original field if the requested translation is not
                available.

        Returns:
            the name of the annotation.
        '''
        assert field_name.startswith(original_field)

        if original_field not in self.get_translatable_fields():
            raise FieldError('Field ({}) is not defined as translatable'.format(original_field))

        if fallback:
            # fallback to the original untranslated field
            field = Coalesce(RawSQL('i18n->>%s', (field_name, )), original_field, output_field=TextField())
        else:
            field = Cast(RawSQL('i18n->>%s', (field_name, )), TextField())

        annotation_field_name = '{}_annotation'.format(field_name)
        self.query.add_annotation(field, annotation_field_name)

        return annotation_field_name

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
        Annotate translated fields before sorting.

        Examples:
         - sort on `-title_nl` will add an annotation for `title_nl`
         - sort on `title_i18n` will add an annotation for the current language

        The field names pointing to translated fields in the `field_names`
        argument will be replaced by their annotated versions.
        '''
        new_field_names = []

        for field in field_names:
            if '_' not in field:
                new_field_names.append(field)
                continue

            # remove descending prefix, not relevant for the annotation
            if field[0] == '-':
                field = field[1:]
                descending = True
            else:
                descending = False

            original_field, language = split_translated_fieldname(field)

            # sort by current language if <original_field>_i18n is requested
            if language == 'i18n':
                language = get_language()
                field = build_localized_fieldname(original_field, language)

            if language == settings.DEFAULT_LANGUAGE:
                sort_field_name = original_field
            else:
                sort_field_name = self.add_i18n_annotation(original_field, field, fallback=True)

            # re-add the descending prefix to the annotated field name
            if descending:
                sort_field_name = '-' + sort_field_name

            new_field_names.append(sort_field_name)

        return super(MultilingualQuerySet, self).order_by(*new_field_names)

    def rewrite_expression(self, lookup, value):
        requested_field_name = lookup
        query_type = ''

        # strip the query type
        if '__' in lookup:
            lookup = lookup[0:lookup.rfind('__')]
            query_type = requested_field_name[len(lookup):]

        original_field, language = split_translated_fieldname(lookup)
        if original_field not in self.get_translatable_fields():
            return requested_field_name, value

        if language == 'i18n':
            # search for current language, including fallback to
            # settings.DEFAULT_LANGUAGE
            language = get_language()
            lookup = build_localized_fieldname(original_field, language)
            fallback = True
        else:
            fallback = False

        if language == settings.DEFAULT_LANGUAGE:
            filter_field_name = original_field
        else:
            filter_field_name = self.add_i18n_annotation(original_field, lookup, fallback=fallback)

        # re-add query type
        filter_field_name += query_type

        return filter_field_name, value

    def rewrite_Q(self, q):
        if isinstance(q, models.Q):
            return models.Q._new_instance(
                list(self.rewrite_Q(child) for child in q.children),
                connector=q.connector,
                negated=q.negated
            )
        if isinstance(q, (list, tuple)):
            return self.rewrite_expression(*q)

    def _filter_or_exclude(self, negate, *args, **kwargs):
        '''
        Annotate filter/exclude fields before filtering.

        Examples:
            - `title_nl__contains='foo'` will add an annotation for `title_nl`
            - `title_nl='bar'` will add an annotation for `title_nl`
            - `title_i18n='foo'` will add an annotation for `title_<language>`
              where `<language>` is the current active language.
            - `Q(title_nl__contains='foo') will add an annotation for `title_nl`

        In all cases, the field part of the field lookup will be changed to use
        the annotated verion.
        '''
        # TODO: handle F expressions in the righthand (value) side of filters

        # handle Q expressions
        new_args = []
        for arg in args:
            new_args.append(self.rewrite_Q(arg))

        # handle the kwargs
        new_kwargs = {}
        for field, value in kwargs.items():
            new_kwargs.update(dict((self.rewrite_expression(field, value), )))

        return super(MultilingualQuerySet, self)._filter_or_exclude(negate, *new_args, **new_kwargs)


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
