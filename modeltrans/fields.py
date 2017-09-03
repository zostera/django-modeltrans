# -*- coding: utf-8 -*-

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ImproperlyConfigured
from django.db.models import fields
from django.db.models.expressions import RawSQL
from django.db.models.functions import Cast, Coalesce
from django.utils.translation import ugettext as _

from .settings import get_default_language, get_fallback_chain
from .utils import build_localized_fieldname, get_language

SUPPORTED_FIELDS = (
    fields.CharField,
    fields.TextField,
)

DEFAULT_LANGUAGE = get_default_language()


def translated_field_factory(original_field, language=None, *args, **kwargs):
    if not isinstance(original_field, SUPPORTED_FIELDS):
        raise ImproperlyConfigured(
            '{} is not supported by django-modeltrans.'.format(original_field.__class__.__name__)
        )

    class Specific(TranslatedVirtualField, original_field.__class__):
        pass

    Specific.__name__ = 'Translated{}'.format(original_field.__class__.__name__)

    return Specific(original_field, language, *args, **kwargs)


class TranslatedVirtualField(object):
    '''
    A field representing a single field translated to a specific language.

    Arguments:
        original_field: The original field to be translated
        language: The lanuage to translate to, or `None` to track the current
            active Django language.
    '''
    # Implementation inspired by HStoreVirtualMixin from:
    # https://github.com/djangonauts/django-hstore/blob/master/django_hstore/virtual.py

    def __init__(self, original_field, language=None, *args, **kwargs):
        # TODO: this feels like a big hack.
        self.__dict__.update(original_field.__dict__)

        self.original_field = original_field
        self.language = language

        self.blank = kwargs['blank']
        self.null = kwargs['null']
        self.editable = kwargs.get('editable', True)

        self.concrete = False

    @property
    def original_name(self):
        return self.original_field.name

    def contribute_to_class(self, cls, name):
        self.model = cls

        self.attname = name
        self.name = name
        self.column = None

        # Use a translated verbose name:
        translated_field_name = _(self.original_field.verbose_name)
        if self.language is not None:
            translated_field_name += ' ({})'.format(self.language.upper())
        self.verbose_name = translated_field_name

        setattr(cls, name, self)
        cls._meta.add_field(self, private=True)

    def db_type(self, connection):
        return None

    def __get__(self, instance, instance_type=None):
        # this method is apparantly called with instance=None from django.
        # django-hstor raises AttributeError here, but that doesn't solve
        # our problem.
        if instance is None:
            return

        language = self.get_language()
        if language == DEFAULT_LANGUAGE:
            return getattr(instance, self.original_name)

        # Make sure we test for containment in a dict, not in None
        if instance.i18n is None:
            instance.i18n = {}

        field_name = build_localized_fieldname(self.original_name, language)

        def has_field(field_name):
            return field_name in instance.i18n and instance.i18n[field_name]

        # in two cases, just return the value:
        #  - if this is an explicit field (<name>_<lang>)
        #  - if this is a implicit field (<name>_i18n) AND the value exists and is not Falsy
        if self.language is not None or has_field(field_name):
            return instance.i18n.get(field_name)

        # this is the _i18n version of the field, and the current language is not available,
        # so we walk the fallback chain:
        for fallback_language in get_fallback_chain(language):
            field_name = build_localized_fieldname(self.original_name, fallback_language)

            if has_field(field_name):
                return instance.i18n.get(field_name)

        # finally, return the original field if all else fails.
        return getattr(instance, self.original_name)

    def __set__(self, instance, value):
        if instance.i18n is None:
            instance.i18n = {}

        language = self.get_language()

        if language == DEFAULT_LANGUAGE:
            setattr(instance, self.original_name, value)
        else:
            field_name = build_localized_fieldname(self.original_name, language)

            # if value is None, remove field from `i18n`.
            if value is None:
                instance.i18n.pop(field_name, None)
            else:
                instance.i18n[field_name] = value

    def get_field_name(self):
        '''
        Returns the field name for the current virtual field.

        The field name is ``<original_field_name>_<language>`` in case of a specific
        translation or ``<original_field_name>_i18n`` for the currently active language.
        '''
        if self.language is None:
            lang = 'i18n'
        else:
            lang = self.get_language()

        return build_localized_fieldname(self.original_name, lang)

    def get_language(self):
        '''
        Returns the language for this field.

        In case of an explicit language (title_en), it returns 'en', in case of
        `title_i18n`, it returns the currently active Django language.
        '''
        return self.language if self.language is not None else get_language()

    def output_field(self):
        '''
        The type of field used to Cast/Coalesce to.

        Mainly because a max_length argument is required for CharField
        until this PR is merged: https://github.com/django/django/pull/8758
        '''
        Field = self.original_field.__class__
        if isinstance(self.original_field, fields.CharField):
            return Field(max_length=self.original_field.max_length)

        return Field()

    def _localized_lookup(self, language):
        if language == DEFAULT_LANGUAGE:
            return self.original_name

        name = build_localized_fieldname(self.original_name, language)
        return RawSQL('{}.i18n->>%s'.format(self.model._meta.db_table), (name, ))

    def sql_lookup(self, fallback=True):
        '''
        Compose the sql lookup to get the value for this virtual field in a query.
        '''

        language = self.get_language()
        if language == DEFAULT_LANGUAGE:
            return self.original_name

        if fallback:
            fallback_chain = get_fallback_chain(language)
            # first, add the current language to the list of lookups
            lookups = [self._localized_lookup(language)]
            # and now, add the list of fallback languages to the lookup list
            for fallback_language in fallback_chain:
                lookups.append(
                    self._localized_lookup(fallback_language)
                )
            return Coalesce(*lookups, output_field=self.output_field())
        else:
            i18n_lookup = self._localized_lookup(language)
            return Cast(i18n_lookup, self.output_field())


class TranslationField(JSONField):
    '''
    This model field is used to store the translations in the translated model.

    Arguments:
        fields (iterable): List of column names to make translatable.
        required_languages (iterable): List of languages required for the model.
        virtual_fields (bool): If False, do not add virtual fields to access
            translated values with.
            Set to `True` during migration from django-modeltranslation to prevent
            collisions with it's database fields while having the `i18n` field available.
    '''
    description = 'Translation storage for a model'

    def __init__(self, fields=None, required_languages=None, virtual_fields=True, *args, **kwargs):
        self.fields = fields or ()
        self.required_languages = required_languages or ()
        self.virtual_fields = virtual_fields

        kwargs['editable'] = False
        kwargs['null'] = True
        super(TranslationField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(TranslationField, self).deconstruct()

        del kwargs['editable']
        del kwargs['null']
        kwargs['fields'] = self.fields
        kwargs['required_languages'] = self.required_languages
        kwargs['virtual_fields'] = self.virtual_fields

        return name, path, args, kwargs

    def contribute_to_class(self, cls, name):
        if name != 'i18n':
            raise ImproperlyConfigured('{} must have name "i18n"'.format(self.__class__.__name__))

        super(TranslationField, self).contribute_to_class(cls, name)
