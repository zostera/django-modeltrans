# -*- coding: utf-8 -*-

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

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
            return getattr(instance, self.original_field)
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


class TranslationJSONField(JSONField):
    description = 'Translation storage for a model'

    def __init__(self, translation_options, *args, **kwargs):
        self.translation_options = translation_options

        kwargs['editable'] = False
        kwargs['null'] = True
        super(TranslationJSONField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(TranslationJSONField, self).deconstruct()

        del kwargs['editable']
        del kwargs['null']

        if self.translation_options is not None:
            kwargs['translation_options'] = self.translation_options

        return name, path, args, kwargs

    def validate(self, value, model_instance):
        '''
        We must override `validate()` to validate even if the value is {}.

        `{}` is considered an empty value, so validation is skipped for parents's
        `validate()` method.
        '''
        opts = self.translation_options

        for field in value.keys():
            original_field = field[0:field.rfind('_')]
            if original_field not in opts.local_fields.keys():
                raise ValidationError(
                    'Key "{}" does not belong to a translatable field'.format(field))

        if isinstance(opts.required_languages, (tuple, list)):
            for lang in opts.required_languages:
                for field in opts.local_fields.keys():
                    if build_localized_fieldname(field, lang) not in value:
                        raise ValidationError(
                            'Translation for field "{}" in "{}" is required'.format(field, lang)
                        )
        else:
            raise NotImplementedError(
                'Validation of required fields not yet implemented for the dict syntax of required_fields'
            )

        return super(TranslationJSONField, self).validate(value, model_instance)
