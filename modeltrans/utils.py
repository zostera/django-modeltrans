from django.contrib.postgres.fields.jsonb import KeyTransform
from django.core.exceptions import FieldDoesNotExist
from django.db.models.constants import LOOKUP_SEP
from django.db.models.lookups import Transform
from django.utils.translation import get_language as _get_language

from .conf import get_available_languages, get_default_language


def get_language():
    """
    Return an active language code that is guaranteed to be in settings.LANGUAGES

    (Django does not seem to guarantee this for us.)
    """
    lang = _get_language()
    if lang in get_available_languages():
        return lang
    return get_default_language()


def split_translated_fieldname(field_name):
    _pos = field_name.rfind("_")
    return (field_name[0:_pos], field_name[_pos + 1 :])


def build_localized_fieldname(field_name, lang):
    if lang == "id":
        # The 2-letter Indonesian language code is problematic with the
        # current naming scheme as Django foreign keys also add "id" suffix.
        lang = "ind"
    return "{}_{}".format(field_name, lang.replace("-", "_"))


def get_model_field(model, path):
    """
    Return the django model field for model in context, following relations.
    """

    if not hasattr(model, "_meta"):
        raise ValueError("Argument 'Model' must be a django.db.models.Model instance.")

    field = None
    for bit in path.split(LOOKUP_SEP):
        try:
            field = model._meta.get_field(bit)
        except FieldDoesNotExist:
            return None

        if hasattr(field, "remote_field"):
            rel = getattr(field, "remote_field", None)
            model = getattr(rel, "model", model)

    return field


def get_instance_field_value(instance, path):
    """
    Return the value of a field or related field for a model instance.
    """
    value = instance
    for bit in path.split(LOOKUP_SEP):
        try:
            value = getattr(value, bit)
        except AttributeError:
            return None

    return value


class FallbackTransform(Transform):
    """
    Custom version of KeyTextTransform to use a database field as part of the key.

    For example: with default_language="nl", calling
    `FallbackTransform("title_", F("fallback_language"), "i18n")` becomes in SQL"
        `"i18n"->>('title_' || "fallback_language")`
    """

    def __init__(self, field_prefix, language_expression, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_prefix = field_prefix
        self.language_expression = language_expression

    def preprocess_lhs(self, compiler, connection, lhs_only=False):
        if not lhs_only:
            key_transforms = [self.field_prefix]
        previous = self.lhs
        while isinstance(previous, KeyTransform):
            if not lhs_only:
                key_transforms.insert(0, previous.key_name)
            previous = previous.lhs
        lhs, params = compiler.compile(previous)
        return (lhs, params, key_transforms) if not lhs_only else (lhs, params)

    def as_postgresql(self, compiler, connection):
        lhs, params, key_transforms = self.preprocess_lhs(compiler, connection)
        params.extend([self.field_prefix])

        rhs = self.language_expression.resolve_expression(compiler.query)
        rhs_sql, rhs_params = compiler.compile(rhs)
        params.extend(rhs_params)

        return "(%s ->> (%%s || %s ))" % (lhs, rhs_sql), (params)
