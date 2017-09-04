# -*- coding: utf-8 -*-

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import F, TextField
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast

from .conf import get_default_language
from .fields import TranslatedVirtualField, TranslationField
from .utils import split_translated_fieldname


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
    for field_name, value in fields.items():
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            ret[field_name] = value
            continue
        if isinstance(field, TranslationField):
            continue

        if isinstance(field, TranslatedVirtualField):
            if field.get_language() == get_default_language():
                if field.original_name in fields:
                    raise ValueError(
                        'Attempted override of "{}" with "{}". '
                        'Only one of the two is allowed.'.format(field.original_name, field_name)
                    )
                ret[field.original_name] = value
            else:
                ret['i18n'][field.name] = value
        else:
            ret[field_name] = value

    return ret


class MultilingualQuerySet(models.query.QuerySet):
    '''
    Extends `~django.db.models.query.Queryset` and makes the translated versions of fields
    accessible through the normal queryset methods, analogous to the virtual fields added
    to a translated model:

     - `<field>` allow getting/setting the default language
     - ``<field>_<lang>`` (for example, `<field>_de`) allows getting/setting a specific language.
       Note that if `LANGUAGE_CODE == 'en'`, `<field>_en` is mapped to `<field>`.
     - `<field>_i18n` follows the currently active translation in Django, and falls back to the default language.

    When adding the `modeltrans.fields.TranslationField` to a model, MultilingualManager is automatically
    mixed in to the manager class of that model.
    '''

    def add_i18n_annotation(self, field, annotation_name=None, fallback=True):
        '''
        Private method to add an annotation to the query to extract the translated
        version of a field from the jsonb field to allow filtering and ordering.

        Arguments:
            field (TranslatedVirtualField): the virtual field to create an annotation for.
            annotation_name (str): name of the annotation, if None (by default),
                `<original_field>_<lang>_annotation` will be used.
            fallback (bool): If `True`, `COALESCE` will be used to get the value
                of the original field if the requested translation is not in the
                `i18n` dict.

        Returns:
            the name of the annotation.
        '''
        annotation = field.sql_lookup(fallback)
        if isinstance(annotation, str):
            return annotation

        if field.model is not self.model and annotation_name is not None:
            # strip the language to make sure Django properly joins the tables.
            # ie: when the lookup is `category__name_nl`, we add an annotation
            # for placeholder=Cast('category__name').
            # This has the side-effect that Django properly joins the tables,
            # but in case of values(), it is not added to the final query.
            lookup_with_original_field = annotation_name[:annotation_name.rfind(field.name)] + field.original_name
            self.query.add_annotation(
                Cast(lookup_with_original_field, TextField()), 'related_annotation_helper'
            )

        if annotation_name is None:
            annotation_name = '{}_annotation'.format(field.name)

        self.query.add_annotation(annotation, annotation_name)
        return annotation_name

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

        for field_name in field_names:
            if '_' not in field_name:
                new_field_names.append(field_name)
                continue

            # remove descending prefix, not relevant for the annotation
            sort_order = ''
            if field_name[0] == '-':
                field_name = field_name[1:]
                sort_order = '-'

            field = self.model._meta.get_field(field_name)
            if not isinstance(field, TranslatedVirtualField):
                new_field_names.append(sort_order + field_name)
                continue

            sort_field_name = self.add_i18n_annotation(field, fallback=True)

            new_field_names.append(sort_order + sort_field_name)

        return super(MultilingualQuerySet, self).order_by(*new_field_names)

    def rewrite_expression(self, lookup, value):
        requested_field_name = lookup
        query_type = ''

        value = self.rewrite_F(value)

        # strip the query type
        # TODO: this is going wrong if a related lookup is used.
        # ie category__name.
        # probably fixable by looking at the
        if '__' in lookup:
            lookup = lookup[0:lookup.rfind('__')]
            query_type = requested_field_name[len(lookup):]

        # special case for pk, because it is not a field.
        if lookup == 'pk':
            return requested_field_name, value

        try:
            field = self.model._meta.get_field(lookup)
        except FieldDoesNotExist:
            return requested_field_name, value

        if not isinstance(field, TranslatedVirtualField):
            return requested_field_name, value

        fallback = field.language is None
        filter_field_name = self.add_i18n_annotation(field, fallback=fallback)

        # re-add query type
        filter_field_name += query_type

        return filter_field_name, value

    def rewrite_F(self, f):
        if not isinstance(f, F):
            return f
        field = self._get_field(f.name)
        rewritten = self.add_i18n_annotation(field, fallback=False)

        return F(rewritten)

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
        Annotate lookups for `filter()` and `exclude()`.

        Examples:
            - `title_nl__contains='foo'` will add an annotation for `title_nl`
            - `title_nl='bar'` will add an annotation for `title_nl`
            - `title_i18n='foo'` will add an annotation for a coalesce of the
               current active language, and all items of the fallback chain.
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

    def _get_field(self, lookup):
        model = self.model

        field = None
        for part in lookup.split(LOOKUP_SEP):
            try:
                field = model._meta.get_field(part)
            except FieldDoesNotExist:
                break

            if hasattr(field, 'remote_field'):
                rel = getattr(field, 'remote_field', None)
                model = getattr(rel, 'model', model)

        return field

    def _values(self, *fields, **expressions):
        '''
        Annotate lookups for `values()` and `values_list()`

        It must be possible to use `Blogs.objects.all().values_list('title_i18n', 'title_nl', 'title_en')`
        '''
        _fields = fields + tuple(expressions)

        for field_name in _fields:
            field = self._get_field(field_name)
            if not isinstance(field, TranslatedVirtualField):
                continue

            fallback = field.language is None

            if field.get_language() == get_default_language():
                # TODO: see if we can just do this with add_i18n_annotation()
                self.query.add_annotation(Cast(field.original_name, field.output_field()), field_name)
            else:
                self.add_i18n_annotation(
                    field,
                    annotation_name=field_name,
                    fallback=fallback
                )

        return super(MultilingualQuerySet, self)._values(*fields, **expressions)


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
    '''
    When adding the `modeltrans.fields.TranslationField` to a model, MultilingualManager is automatically
    mixed in to the manager class of that model.
    '''
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
