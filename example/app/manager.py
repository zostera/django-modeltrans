import itertools

from django.db import models
from django.db.models import FieldDoesNotExist
from django.utils.six import moves

from .utils import build_localized_fieldname, get_language, resolution_order


def get_translatable_fields_for_model(model):
    return getattr(model, 'translatable', None)


def rewrite_lookup_key(model, lookup_key):
    pieces = lookup_key.split('__', 1)
    original_key = pieces[0]

    translatable_fields = get_translatable_fields_for_model(model)
    if translatable_fields is not None:
        # If we are doing a lookup on a translatable field,
        # we want to rewrite it to the actual field name
        # For example, we want to rewrite "name__startswith" to "name_fr__startswith"
        if pieces[0] in translatable_fields:
            pieces[0] = build_localized_fieldname(pieces[0], get_language())

    if len(pieces) > 1:
        # Check if we are doing a lookup to a related trans model
        fields_to_trans_models = get_fields_to_translatable_models(model)
        # Check ``original key``, as pieces[0] may have been already rewritten.
        if original_key in fields_to_trans_models:
            transmodel = fields_to_trans_models[original_key]
            pieces[1] = rewrite_lookup_key(transmodel, pieces[1])
    return '__'.join(pieces)


def append_fallback(model, fields):
    """
    If translated field is encountered, add also all its fallback fields.
    Returns tuple: (set_of_new_fields_to_use, set_of_translated_field_names)
    """
    fields = set(fields)
    trans = set()
    from modeltranslation.translator import translator
    opts = translator.get_options_for_model(model)
    for key, _ in opts.fields.items():
        if key in fields:
            langs = resolution_order(get_language(), getattr(model, key).fallback_languages)
            fields = fields.union(build_localized_fieldname(key, lang) for lang in langs)
            fields.remove(key)
            trans.add(key)
    return fields, trans


def append_translated(model, fields):
    "If translated field is encountered, add also all its translation fields."
    fields = set(fields)
    from modeltranslation.translator import translator
    opts = translator.get_options_for_model(model)
    for key, translated in opts.fields.items():
        if key in fields:
            fields = fields.union(f.name for f in translated)
    return fields


def append_lookup_key(model, lookup_key):
    "Transform spanned__lookup__key into all possible translation versions, on all levels"
    pieces = lookup_key.split('__', 1)

    fields = append_translated(model, (pieces[0],))

    if len(pieces) > 1:
        # Check if we are doing a lookup to a related trans model
        fields_to_trans_models = get_fields_to_translatable_models(model)
        if pieces[0] in fields_to_trans_models:
            transmodel = fields_to_trans_models[pieces[0]]
            rest = append_lookup_key(transmodel, pieces[1])
            fields = set('__'.join(pr) for pr in itertools.product(fields, rest))
        else:
            fields = set('%s__%s' % (f, pieces[1]) for f in fields)
    return fields


def append_lookup_keys(model, fields):
    return moves.reduce(set.union, (append_lookup_key(model, field) for field in fields), set())


def rewrite_order_lookup_key(model, lookup_key):
    if lookup_key.startswith('-'):
        return '-' + rewrite_lookup_key(model, lookup_key[1:])
    else:
        return rewrite_lookup_key(model, lookup_key)

_F2TM_CACHE = {}


def get_fields_to_translatable_models(model):
    if model in _F2TM_CACHE:
        return _F2TM_CACHE[model]

    results = []
    for f in model._meta.get_fields():
        if f.is_relation and f.related_model:
            # The new get_field() will find GenericForeignKey relations.
            # In that case the 'related_model' attribute is set to None
            # so it is necessary to check for this value before trying to
            # get translatable fields.
            if get_translatable_fields_for_model(f.related_model) is not None:
                results.append((f.name, f.related_model))
    _F2TM_CACHE[model] = dict(results)
    return _F2TM_CACHE[model]

_C2F_CACHE = {}


def get_field_by_colum_name(model, col):
    # First, try field with the column name
    try:
        field = model._meta.get_field(col)
        if field.column == col:
            return field
    except FieldDoesNotExist:
        pass
    field = _C2F_CACHE.get((model, col), None)
    if field:
        return field
    # D'oh, need to search through all of them.
    for field in model._meta.fields:
        if field.column == col:
            _C2F_CACHE[(model, col)] = field
            return field
    assert False, 'No field found for column %s' % col


class MultilingualQuerySet(models.query.QuerySet):
    def _post_init(self):
        return

    def _rewrite_applied_operations(self):
        return

    def order_by(self, *field_names):
        print field_names
        transformed = []
        for field in field_names:
            transformed.append(field)

        super(MultilingualQuerySet, self).order_by(*transformed)


def multilingual_queryset_factory(old_cls, instantiate=True):
    '''Mix MultilingualQuerySet in custom QuerySets.'''
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
