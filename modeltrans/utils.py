from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.translation import get_language as _get_language

from modeltrans import settings


def get_default_language():
    '''
    Returns the default language for modeltrans, based on the django setting
    LANGUAGE_CODE.

    Note that changing the LANGUAGE_CODE of an existing application will result
    in inconsistant data because the value of the original field is assumed to
    be in the default language.
    '''
    return settings.LANGUAGE_CODE.split('-')[0]


def get_language():
    '''
    Return an active language code that is guaranteed to be in
    settings.LANGUAGES (Django does not seem to guarantee this for us).
    '''
    lang = _get_language()
    default_language = get_default_language()

    if lang is None:  # Django >= 1.8
        return settings.DEFAULT_LANGUAGE
    if lang not in settings.MODELTRANS_AVAILABLE_LANGUAGES and '-' in lang:
        lang = lang.split('-')[0]
    if lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
        return lang
    return settings.DEFAULT_LANGUAGE


def get_available_languages():
    '''
    Returns the list of available languages for django-modeltrans.
    '''
    return list(settings.MODELTRANS_AVAILABLE_LANGUAGES) + list((get_default_language(), ))


def get_translation_fields(field):
    '''
    Returns a list of localized fieldnames for a given field.
    '''
    return [build_localized_fieldname(field, l) for l in settings.MODELTRANS_AVAILABLE_LANGUAGES]


def split_translated_fieldname(field_name):
    _pos = field_name.rfind('_')
    return (field_name[0:_pos], field_name[_pos + 1:])


def build_localized_fieldname(field_name, lang):
    if lang == 'id':
        # The 2-letter Indonesian language code is problematic with the
        # current naming scheme as Django foreign keys also add "id" suffix.
        lang = 'ind'
    return str('{}_{}'.format(field_name, lang.replace('-', '_')))


def _build_localized_verbose_name(verbose_name, lang):
    if lang == 'id':
        lang = 'ind'
    return force_text('%s [%s]') % (force_text(verbose_name), lang)


build_localized_verbose_name = lazy(_build_localized_verbose_name, six.text_type)
