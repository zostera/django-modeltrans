# -*- coding: utf-8 -*-

from .settings import DEFAULT_LANGUAGE
from .utils import build_localized_fieldname, get_language


class TranslationFieldProxy(object):
    '''
    Descriptor for a translation field, pointing to a specific language.
    '''
    def __init__(self, model, original_field, language):
        self.model = model

        self.original_field = original_field
        self.language = language

    def __get__(self, instance=None, owner=None):
        if self.get_language() == DEFAULT_LANGUAGE:
            return getattr(instance, self.original_field)

        key = self.get_field_name()
        if key not in instance.i18n:
            # TODO: implement fallback
            raise AttributeError(
                "'{}.{}' has no translation '{}'".format(
                    instance.__class__.__name__,
                    self.original_field,
                    self.get_language()
                )
            )
        return instance.i18n[key]

    def __set__(self, instance, value):
        if self.get_language() == DEFAULT_LANGUAGE:
            setattr(instance, self.original_field, value)
            return

        instance.i18n[self.get_field_name()] = value

    def get_language(self):
        return self.language

    def get_field_name(self):
        return build_localized_fieldname(self.original_field, self.get_language())


class ActiveTranslationFieldProxy(TranslationFieldProxy):
    '''
    Descriptor for a translation field, pointing to the active language.
    '''

    def __init__(self, model, original_field):
        self.model = model
        self.original_field = original_field

    def get_language(self):
        return get_language()
