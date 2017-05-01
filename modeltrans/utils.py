from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.translation import get_language as _get_language

from modeltrans import settings


def get_language():
    '''
    Return an active language code that is guaranteed to be in
    settings.LANGUAGES (Django does not seem to guarantee this for us).
    '''
    lang = _get_language()
    if lang is None:  # Django >= 1.8
        return settings.DEFAULT_LANGUAGE
    if lang not in settings.AVAILABLE_LANGUAGES and '-' in lang:
        lang = lang.split('-')[0]
    if lang in settings.AVAILABLE_LANGUAGES:
        return lang
    return settings.DEFAULT_LANGUAGE


def get_translation_fields(field):
    '''
    Returns a list of localized fieldnames for a given field.
    '''
    return [build_localized_fieldname(field, l) for l in settings.AVAILABLE_LANGUAGES]


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
