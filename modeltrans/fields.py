# -*- coding: utf-8 -*-

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext as _

from .settings import DEFAULT_LANGUAGE
from .utils import build_localized_fieldname, get_language


class TranslatedVirtualField(models.CharField):
    '''
    Implementation inspired by HStoreVirtualMixin from:
    https://github.com/djangonauts/django-hstore/blob/master/django_hstore/virtual.py
    '''

    def __init__(self, original_field, language=None, *args, **kwargs):
        # the name of the original field
        self.original_field = original_field
        self.language = language

        kwargs['max_length'] = 255

        super(TranslatedVirtualField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(TranslationJSONField, self).deconstruct()

        del kwargs['max_length']

        if self.model is not None:
            kwargs['original_field'] = self.original_field
            kwargs['language'] = self.language

        return name, path, args, kwargs

    concrete = False

    def contribute_to_class(self, cls, name):
        self.model = cls

        self.attname = name
        self.name = name
        self.column = None

        # Use a translated verbose name:
        original_field = cls._meta.get_field(self.original_field)
        translated_field_name = _(original_field.verbose_name)
        if self.language is not None:
            translated_field_name += ' ({})'.format(self.language.upper())
        self.verbose_name = translated_field_name

        setattr(cls, name, self)
        cls._meta.add_field(self, private=True)

    def db_type(self, connection):
        return None

    def __get__(self, instance, instance_type=None):

        language = self.get_language()
        if language == DEFAULT_LANGUAGE:
            return getattr(instance, self.original_field)

        # Make sure we test for containment in a dict, not in None
        if instance.i18n is None:
            instance.i18n = {}

        # fallback (only for <original_field>_i18n fields)
        field_name = build_localized_fieldname(self.original_field, language)
        if self.language is None and field_name not in instance.i18n:
            return getattr(instance, self.original_field)

        return instance.i18n.get(field_name)

    def __set__(self, instance, value):
        if instance.i18n is None:
            instance.i18n = {}

        if value is None:
            return

        language = self.get_language()

        if language == DEFAULT_LANGUAGE:
            setattr(instance, self.original_field, value)
        else:
            field_name = build_localized_fieldname(self.original_field, language)
            instance.i18n[field_name] = value

    def get_field_name(self):
        '''
        Returns the field name for this virtual field.

        Two options:
            - <original_field>_i18n for the current active language
            - <original_field>_<language> for the specific translation
        '''
        if self.language is None:
            lang = 'i18n'
        else:
            lang = self.get_language()

        return build_localized_fieldname(self.original_field, lang)

    def get_language(self):
        return self.language if self.language is not None else get_language()


class TranslationJSONField(JSONField):
    '''
    This model fields is used to store the translations in the translated model.
    '''
    description = 'Translation storage for a model'

    def __init__(self, *args, **kwargs):
        kwargs['editable'] = False
        kwargs['null'] = True
        super(TranslationJSONField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(TranslationJSONField, self).deconstruct()

        del kwargs['editable']
        del kwargs['null']

        return name, path, args, kwargs
