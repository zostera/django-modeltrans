# -*- coding: utf-8 -*-

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast
from django.utils import six

from .conf import get_default_language
from .fields import TranslatedVirtualField, TranslationField


def transform_translatable_fields(model, fields):
    '''
    Transform the kwargs for a <Model>.objects.create() or <Model>()
    to allow passing translated field names.

    Arguments:
        fields (dict): kwargs to a model __init__ or Model.objects.create() method
            for which the field names need to be translated to values in the i18n field
    '''
    # If the current model does have the TranslationField, we must not apply
    # any transformation for it will result in a:
    # TypeError: 'i18n' is an invalid keyword argument for this function
    if not hasattr(model, 'i18n'):
        return fields

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

    def _add_i18n_annotation(self, virtual_field=None, fallback=True, bare_lookup=None, annotation_name=None):
        '''
        Private method to add an annotation to the query to extract the translated
        version of a field from the jsonb field to allow filtering and ordering.

        Arguments:
            field (TranslatedVirtualField): the virtual field to create an annotation for.
            annotation_name (str): name of the annotation, if None the default
                `<original_field>_<lang>_annotation` will be used

            fallback (bool): If `True`, `COALESCE` will be used to get the value
                of the original field if the requested translation is not in the
                `i18n` dict.

        Returns:
            the name of the annotation created.
        '''
        annotation = virtual_field.as_sql(fallback=fallback, bare_lookup=bare_lookup)
        if isinstance(annotation, six.string_types):
            return annotation

        if annotation_name is None:
            annotation_name = '{}_annotation'.format(virtual_field.name)

        self.query.add_annotation(annotation, annotation_name)
        return annotation_name

    def _get_field(self, lookup):
        '''
        Return the Django model field for a lookup plus the remainder of the lookup,
        which should be the lookup type.
        '''
        field = None
        lookup_type = None

        bits = lookup.split(LOOKUP_SEP)

        model = self.model
        for i, bit in enumerate(bits):
            try:
                field = model._meta.get_field(bit)
            except FieldDoesNotExist:
                lookup_type = LOOKUP_SEP.join(bits[i:])
                break

            if hasattr(field, 'remote_field'):
                rel = getattr(field, 'remote_field', None)
                model = getattr(rel, 'model', model)

        return field, lookup_type

    def _rewrite_filter_clause(self, lookup, value):
        '''
        private method which rewrites a filter clause passed to filter()/exclude()
        etc., for example:

        for title_nl__like='va'
        _rewrite_filter_clause('title_nl__like', 'va') would be called.
        '''
        value = self._rewrite_expression(value)

        # pk not a field, but shorthand for the primary key column.
        if lookup == 'pk':
            return lookup, value

        field, lookup_type = self._get_field(lookup)

        if not isinstance(field, TranslatedVirtualField):
            return lookup, value

        if lookup_type is not None:
            bare_lookup = lookup[0:-(len(LOOKUP_SEP + lookup_type))]
        else:
            bare_lookup = lookup

        filter_field_name = self._add_i18n_annotation(
            virtual_field=field,
            bare_lookup=bare_lookup,
            fallback=field.language is None
        )

        # re-add lookup type
        if lookup_type is not None:
            filter_field_name += LOOKUP_SEP + lookup_type

        return filter_field_name, value

    def _rewrite_expression(self, expr):
        '''
        Rewrite rhs of expressions.
        '''
        if isinstance(expr, models.F):
            field, _ = self._get_field(expr.name)

            if not isinstance(field, TranslatedVirtualField):
                return expr

            return field.as_sql(fallback=False, bare_lookup=expr.name)

        elif isinstance(expr, models.expressions.CombinedExpression):
            return models.expressions.CombinedExpression(
                self._rewrite_expression(expr.lhs),
                expr.connector,
                self._rewrite_expression(expr.rhs)
            )
        elif isinstance(expr, models.Count):
            return models.Count(
                self._rewrite_expression(expr.source_expressions[0])
            )
        elif isinstance(expr, models.Func):
            new_expressions = []
            for expression in expr.source_expressions:
                new_expressions.append(self._rewrite_expression(expression))

            kwargs = {}
            if hasattr(expr, 'output_field'):
                kwargs['output_field'] = expr.output_field

            if hasattr(expr, 'desc') and expr.desc is True:
                kwargs['desc'] = True

            return type(expr)(*new_expressions, **kwargs)
        else:
            return expr

    def _rewrite_Q(self, q):
        if isinstance(q, models.Q):
            return models.Q._new_instance(
                list(self._rewrite_Q(child) for child in q.children),
                connector=q.connector,
                negated=q.negated
            )
        if isinstance(q, (list, tuple)):
            return self._rewrite_filter_clause(*q)

    def _rewrite_ordering(self, field_names):
        new_field_names = []

        for field_name in field_names:
            if not isinstance(field_name, six.string_types):
                new_field_names.append(self._rewrite_expression(field_name))
                continue

            # remove descending prefix, not relevant for the annotation
            sort_order = ''
            if field_name[0] == '-':
                field_name = field_name[1:]
                sort_order = '-'

            if field_name == 'pk':
                new_field_names.append(sort_order + 'pk')
                continue

            field, lookup_type = self._get_field(field_name)
            if field is None or not isinstance(field, TranslatedVirtualField):
                # if the field is just a normal field or not a field
                # no rewriting needed
                new_field_names.append(sort_order + field_name)
                continue

            assert lookup_type is None, '{} is not a valid order_by lookup'.format(field_name)

            sort_field = field.as_sql(bare_lookup=field_name)
            if isinstance(sort_field, six.string_types):
                new_field_names.append(sort_order + sort_field)
                continue
            elif sort_order == '-':
                sort_field = sort_field.desc()

            new_field_names.append(sort_field)

        return new_field_names

    def annotate(self, *args, **kwargs):
        '''
        Patch annotate to allow the use of translated field names in annotations.

        https://docs.djangoproject.com/en/1.11/ref/models/querysets/#annotate
        '''
        args = [self._rewrite_expression(a) for a in args]
        kwargs = {alias: self._rewrite_expression(expr) for alias, expr in kwargs.items()}

        return super(MultilingualQuerySet, self).annotate(*args, **kwargs)

    def create(self, **kwargs):
        '''
        Patch the create method to allow adding the value for a translated field
        using `Model.objects.create(..., title_nl='...')`.

        https://docs.djangoproject.com/en/1.11/ref/models/querysets/#create
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

        https://docs.djangoproject.com/en/1.11/ref/models/querysets/#order_by
        '''

        new_field_names = self._rewrite_ordering(field_names)

        return super(MultilingualQuerySet, self).order_by(*new_field_names)

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

        # handle Q expressions / args
        new_args = []
        for arg in args:
            new_args.append(self._rewrite_Q(arg))

        # handle the kwargs
        new_kwargs = {}
        for field, value in kwargs.items():
            new_kwargs.update(dict((self._rewrite_filter_clause(field, value), )))

        return super(MultilingualQuerySet, self)._filter_or_exclude(negate, *new_args, **new_kwargs)

    def _values(self, *fields, **expressions):
        '''
        Annotate lookups for `values()` and `values_list()`

        It must be possible to use:
        `Blogs.objects.all().values_list('title_i18n', 'title_nl', 'title_en')`

        But also spanning relations:
        `Blogs.objects.all().values_list('title_i18n', 'category__name__i18n')`
        '''
        _fields = fields + tuple(expressions)

        for field_name in _fields:
            field, lookup_type = self._get_field(field_name)
            if not isinstance(field, TranslatedVirtualField):
                continue

            fallback = field.language is None

            if field.get_language() == get_default_language():
                original_field = field_name.replace(field.name, field.original_field.name)
                self.query.add_annotation(Cast(original_field, field.output_field()), field_name)
            else:
                self._add_i18n_annotation(
                    virtual_field=field,
                    fallback=fallback,
                    bare_lookup=field_name,
                    annotation_name=field_name
                )

        return super(MultilingualQuerySet, self)._values(*fields, **expressions)

    def __reduce__(self):
        '''
        Make sure a dynamic version of this class can be pickled
        '''
        return multilingual_queryset_factory, (self.__class__.__bases__[0],), self.__getstate__()


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
