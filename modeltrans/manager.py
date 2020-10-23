from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count, Func, Manager, Q, QuerySet
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import CombinedExpression, F, OrderBy
from django.db.models.functions import Cast

from .conf import get_default_language
from .fields import TranslatedVirtualField


def transform_translatable_fields(model, fields):
    """
    Transform the kwargs for a <Model>.objects.create() or <Model>()
    to allow passing translated field names.

    Arguments:
        fields (dict): kwargs to a model __init__ or Model.objects.create() method
            for which the field names need to be translated to values in the i18n field
    """
    # If the current model does have the TranslationField, we must not apply
    # any transformation for it will result in a:
    # TypeError: 'i18n' is an invalid keyword argument for this function
    if not hasattr(model, "i18n"):
        return fields

    ret = {"i18n": fields.pop("i18n", None) or {}}

    # keep track of translated fields, and do not return an `i18n` key if no
    # translated fields are found.
    has_translated_fields = len(ret["i18n"].items()) > 0

    for field_name, value in fields.items():
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            ret[field_name] = value
            continue

        if isinstance(field, TranslatedVirtualField):
            has_translated_fields = True
            if field.get_language() == get_default_language():
                if field.original_name in fields:
                    raise ValueError(
                        'Attempted override of "{}" with "{}". '
                        "Only one of the two is allowed.".format(field.original_name, field_name)
                    )
                ret[field.original_name] = value
            else:
                ret["i18n"][field.name] = value
        else:
            ret[field_name] = value

    if not has_translated_fields:
        return fields

    return ret


class MultilingualQuerySet(QuerySet):
    """
    Extends ``~django.db.models.query.QuerySet`` and makes the translated versions of fields
    accessible through the normal QuerySet methods, analogous to the virtual fields added
    to a translated model:

     - `<field>` allow getting/setting the default language
     - ``<field>_<lang>`` (for example, `<field>_de`) allows getting/setting a specific language.
       Note that if `LANGUAGE_CODE == "en"`, `<field>_en` is mapped to `<field>`.
     - `<field>_i18n` follows the currently active translation in Django, and falls back to the default language.

    When adding the `modeltrans.fields.TranslationField` to a model, MultilingualManager is automatically
    mixed in to the manager class of that model.
    """

    def _add_i18n_annotation(
        self, virtual_field=None, fallback=True, bare_lookup=None, annotation_name=None
    ):
        """
        Private method to add an annotation to the query to extract the translated
        version of a field from the jsonb field to allow filtering and ordering.

        Arguments:
            virtual_field (TranslatedVirtualField): the virtual field to create an annotation for.
            fallback (bool): If `True`, `COALESCE` will be used to get the value of the original
                field if the requested translation is not in the `i18n` dict.
            bare_lookup:
            annotation_name (str): name of the annotation, if None the default
                `<original_field>_<lang>_annotation` will be used.

        Returns:
            the name of the annotation created.
        """
        expression = virtual_field.as_expression(fallback=fallback, bare_lookup=bare_lookup)

        if isinstance(expression, F):
            return expression.name

        if annotation_name is None:
            annotation_name = "{}_annotation".format(virtual_field.name)

        self.query.add_annotation(expression, annotation_name)
        return annotation_name

    def _get_field(self, lookup):
        """
        Return the Django model field for a lookup plus the remainder of the lookup,
        which should be the lookup type.
        """
        model = self.model
        lookup_type = None

        # pk is not an actual field, but an alias for the implicit id field.
        if lookup == "pk":
            key = None
            for field in model._meta.get_fields():
                if getattr(field, "primary_key", False):
                    key = field
            return key, None

        field = None
        bits = lookup.split(LOOKUP_SEP)

        for i, bit in enumerate(bits):
            try:
                field = model._meta.get_field(bit)
            except FieldDoesNotExist:
                lookup_type = LOOKUP_SEP.join(bits[i:])
                break

            if hasattr(field, "remote_field"):
                rel = getattr(field, "remote_field", None)
                model = getattr(rel, "model", model)

        return field, lookup_type

    def _rewrite_filter_clause(self, lookup, value):
        """
        Rewrite a filter clause passed to filter()/exclude()/etc.

        for example:

        for title_nl__like="va"
        _rewrite_filter_clause("title_nl__like", "va") should be called.
        """
        value = self._rewrite_expression(value)
        field, lookup_type = self._get_field(lookup)

        if not isinstance(field, TranslatedVirtualField):
            return lookup, value

        if lookup_type is not None:
            bare_lookup = lookup[0 : -(len(LOOKUP_SEP + lookup_type))]
        else:
            bare_lookup = lookup

        filter_field_name = self._add_i18n_annotation(
            virtual_field=field, bare_lookup=bare_lookup, fallback=field.language is None
        )

        # re-add lookup type
        if lookup_type is not None:
            filter_field_name += LOOKUP_SEP + lookup_type

        return filter_field_name, value

    def _rewrite_expression(self, expr):
        """
        Rewrite expressions.

        https://docs.djangoproject.com/en/stable/ref/models/expressions/

        This current way of doing this is bound to lag behind any new things implemented in Django.
        It would be really nice to have a better/more generic way of doing this.
        """
        if isinstance(expr, F):
            field, _ = self._get_field(expr.name)
            if not isinstance(field, TranslatedVirtualField):
                return expr

            return field.as_expression(fallback=field.language is None, bare_lookup=expr.name)
        elif isinstance(expr, CombinedExpression):
            expr.lhs = self._rewrite_expression(expr.lhs)
            expr.rhs = self._rewrite_expression(expr.rhs)
        elif isinstance(expr, Count):
            expr.source_expressions[0] = self._rewrite_expression(expr.source_expressions[0])
        elif isinstance(expr, Func):
            expr.source_expressions = list(
                [self._rewrite_expression(e) for e in expr.source_expressions]
            )
        elif isinstance(expr, OrderBy):
            expr.expression = self._rewrite_expression(expr.expression)
        return expr

    def _rewrite_Q(self, q):
        if isinstance(q, Q):
            return Q._new_instance(
                list(self._rewrite_Q(child) for child in q.children),
                connector=q.connector,
                negated=q.negated,
            )
        if isinstance(q, (list, tuple)):
            return self._rewrite_filter_clause(*q)

    def _rewrite_ordering(self, field_names):
        new_field_names = []

        for field_name in field_names:
            if not isinstance(field_name, str):
                new_field_names.append(self._rewrite_expression(field_name))
                continue

            # remove descending prefix, not relevant for the annotation
            sort_order = ""
            if field_name[0] == "-":
                field_name = field_name[1:]
                sort_order = "-"

            if field_name == "pk":
                new_field_names.append(sort_order + "pk")
                continue

            field, lookup_type = self._get_field(field_name)
            if field is None or not isinstance(field, TranslatedVirtualField):
                # if the field is just a normal field or not a field
                # no rewriting needed
                new_field_names.append(sort_order + field_name)
                continue

            assert lookup_type is None, "{} is not a valid order_by lookup".format(field_name)

            sort_field = field.as_expression(bare_lookup=field_name)
            if sort_order == "-":
                sort_field = sort_field.desc()

            new_field_names.append(sort_field)

        return new_field_names

    def annotate(self, *args, **kwargs):
        """
        Patch annotate to allow the use of translated field names in annotations.

        https://docs.djangoproject.com/en/stable/ref/models/querysets/#annotate
        """
        args = [self._rewrite_expression(a) for a in args]
        kwargs = {alias: self._rewrite_expression(expr) for alias, expr in kwargs.items()}

        return super().annotate(*args, **kwargs)

    def create(self, **kwargs):
        """
        Patch the create method to allow adding the value for a translated field
        using `Model.objects.create(..., title_nl="...")`.

        https://docs.djangoproject.com/en/stable/ref/models/querysets/#create
        """
        return super().create(**transform_translatable_fields(self.model, kwargs))

    def order_by(self, *field_names):
        """
        Annotate translated fields before sorting.

        Examples:
         - sort on `-title_nl` will add an annotation for `title_nl`
         - sort on `title_i18n` will add an annotation for the current language

        The field names pointing to translated fields in the `field_names`
        argument will be replaced by their annotated versions.

        https://docs.djangoproject.com/en/1.11/ref/models/querysets/#order_by
        """

        new_field_names = self._rewrite_ordering(field_names)

        return super().order_by(*new_field_names)

    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        Annotate lookups for `filter()` and `exclude()`.

        Examples:
            - `title_nl__contains="foo"` will add an annotation for `title_nl`
            - `title_nl="bar"` will add an annotation for `title_nl`
            - `title_i18n="foo"` will add an annotation for a coalesce of the
               current active language, and all items of the fallback chain.
            - `Q(title_nl__contains="foo") will add an annotation for `title_nl`

        In all cases, the field part of the field lookup will be changed to use
        the annotated verion.
        """
        # handle Q expressions / args
        new_args = []
        for arg in args:
            new_args.append(Q(self._rewrite_Q(arg)))

        # handle the kwargs
        new_kwargs = {}
        for field, value in kwargs.items():
            new_kwargs.update(dict((self._rewrite_filter_clause(field, value),)))

        return super()._filter_or_exclude(negate, *new_args, **new_kwargs)

    def _values(self, *fields, **expressions):
        """
        Annotate lookups for `values()` and `values_list()`

        It must be possible to use:
        `Blogs.objects.all().values_list("title_i18n", "title_nl", "title_en")`

        But also spanning relations:
        `Blogs.objects.all().values_list("title_i18n", "category__name__i18n")`
        """
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
                    annotation_name=field_name,
                )

        return super()._values(*fields, **expressions)

    def __reduce__(self):
        """
        Make sure a dynamic version of this class can be pickled
        """
        return multilingual_queryset_factory, (self.__class__.__bases__[0],), self.__getstate__()


def multilingual_queryset_factory(old_cls, instantiate=True):
    """Return a MultilingualQuerySet, or mix MultilingualQuerySet in custom QuerySets."""
    if old_cls == QuerySet:
        NewClass = MultilingualQuerySet
    else:

        class NewClass(old_cls, MultilingualQuerySet):
            pass

        NewClass.__name__ = "Multilingual%s" % old_cls.__name__
    return NewClass() if instantiate else NewClass


class MultilingualManager(Manager):
    """
    When adding the `modeltrans.fields.TranslationField` to a model, MultilingualManager is automatically
    mixed in to the manager class of that model.

    If you want to use translated fields when building the query from a related model, you need to add
    ``objects = MultilingualManager()`` to the model you want to build the query from.

    For example, ``Category`` needs ``objects = MultilingualManager()`` in order to allow
    ``Category.objects.filter(blog__title_i18n__icontains="django")``::

        class Category(models.Model):
            title = models.CharField(max_length=255)

            objects = MultilingualManager()  # required to use translated fields of Blog.

        class Blog(models.Model):
            title = models.CharField(max_length=255)
            body = models.TextField(null=True)
            category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)

            i18n = TranslationField(fields=("title", "body"))
    """

    use_for_related_fields = True

    def _patch_queryset(self, qs):
        qs.__class__ = multilingual_queryset_factory(qs.__class__, instantiate=False)
        return qs

    def get_queryset(self):
        """
        This method is repeated because some managers that don't use super() or alter the QuerySet class
        may return QuerySet that is not subclass of MultilingualQuerySet.
        """
        qs = super().get_queryset()
        if isinstance(qs, MultilingualQuerySet):
            # Is already patched
            return qs
        return self._patch_queryset(qs)
