# -*- coding: utf-8 -*-

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext as _

from .settings import DEFAULT_LANGUAGE
from .utils import build_localized_fieldname, get_language


class VirtualFieldMixin(object):
    '''
    Implementation inspired by HStoreVirtualMixin from:
    https://github.com/djangonauts/django-hstore/blob/master/django_hstore/virtual.py
    '''
    concrete = False

    def deconstruct(self, *args, **kwargs):
        name, path, args, kwargs = super(VirtualFieldMixin, self).deconstruct(*args, **kwargs)
        return (name, path, args, {'default': kwargs.get('default'), 'to': None})

    def contribute_to_class(self, cls, name):
        self.model = cls

        self.attname = name
        self.name = name
        self.column = None

        setattr(cls, name, self)
        cls._meta.add_field(self, virtual=True)

    def db_type(self, connection):
        return None

    def __get__(self, instance, instance_type=None):
        field = getattr(instance, 'i18n')
        if not field:
            return self.default

        return instance.i18n.get(self.name, self.default)

    def __set__(self, instance, value):
        instance.i18n[self.name] = value

    def get_field_name(self):
        return build_localized_fieldname(self.original_field, self.get_language())

    def get_language(self):
        return self.language if self.language is not None else get_language()

    @property
    def short_description(self):
        return _(self.original_field)


class TranlatedVirtualField(VirtualFieldMixin, models.CharField):

    def __init__(self, original_field, language=None, *args, **kwargs):
        self.original_field = original_field
        self.language = language

        kwargs['max_length'] = 255

        super(TranlatedVirtualField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(TranslationJSONField, self).deconstruct()

        del kwargs['max_length']

        if self.model is not None:
            kwargs['original_field'] = self.original_field
            kwargs['language'] = self.language

        return name, path, args, kwargs

    def __get__(self, instance=None, owner=None):
        if self.get_language() == DEFAULT_LANGUAGE:
            return getattr(instance, self.original_field)

        key = self.get_field_name()
        if key not in instance.i18n:
            return getattr(instance, self.original_field)
        return instance.i18n[key]

    def __set__(self, instance, value):
        if self.get_language() == DEFAULT_LANGUAGE:
            setattr(instance, self.original_field, value)
            return
        instance.i18n[self.get_field_name()] = value



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
