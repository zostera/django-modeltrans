from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.translation import get_language as _get_language
from modeltrans import settings


def get_default_language():
    '''
    Returns the default language for modeltrans, defined in the django setting
    LANGUAGE_CODE.

    Note that changing the LANGUAGE_CODE of an existing application will result
    in inconsistent data because the value of the original field is assumed to
    be in the default language.
    '''
    return settings.LANGUAGE_CODE


def get_language():
    '''
    Return an active language code that is guaranteed to be in
    settings.LANGUAGES (Django does not seem to guarantee this for us).
    '''
    lang = _get_language()

    if lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
        return lang
    return get_default_language()


def get_available_languages(include_default=True):
    '''
    Returns a tuple of available languages for django-modeltrans.
    '''
    if include_default:
        return tuple(set(
            settings.MODELTRANS_AVAILABLE_LANGUAGES +
            tuple((get_default_language(), ))
        ))
    else:
        return settings.MODELTRANS_AVAILABLE_LANGUAGES


def split_translated_fieldname(field_name):
    _pos = field_name.rfind('_')
    return (field_name[0:_pos], field_name[_pos + 1:])


def build_localized_fieldname(field_name, lang):
    if lang == 'id':
        # The 2-letter Indonesian language code is problematic with the
        # current naming scheme as Django foreign keys also add "id" suffix.
        lang = 'ind'
    return str('{}_{}'.format(field_name, lang.replace('-', '_')))
