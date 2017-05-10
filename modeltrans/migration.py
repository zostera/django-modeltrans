# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured

try:
    from modeltranslation.translator import translator
    DJANGO_MODELTRANSLATION_AVAILABLE = True
except ImportError:
    DJANGO_MODELTRANSLATION_AVAILABLE = False


def _raise_if_not_django_modeltranslation():
    if not DJANGO_MODELTRANSLATION_AVAILABLE:
        raise ImproperlyConfigured(
            'django-modeltranslation must be still installed when creating'
            'the modeltranslation -> modeltrans migrations.'
        )


def get_translatable_models():
    _raise_if_not_django_modeltranslation()
    return translator.get_registered_models()


def get_translated_fields(model):
    '''
    Enumerates the translated fields for a model.
    For example: title_nl, title_en, title_fr, body_nl, body_en, body_fr
    '''
    _raise_if_not_django_modeltranslation()

    options = translator.get_options_for_model(model)

    for field in options.field:
        for translated in field.values():
            yield translated.name


def copy_translations(model, fields):
    for m in model.objects.all():
        for field in fields:
            m.i18n[field] = getattr(m, field)

        m.save()
