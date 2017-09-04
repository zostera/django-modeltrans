from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.translation import get_language as _get_language

from .conf import get_available_languages, get_default_language


def get_language():
    '''
    Return an active language code that is guaranteed to be in
    settings.LANGUAGES (Django does not seem to guarantee this for us).
    '''
    lang = _get_language()
    MODELTRANS_AVAILABLE_LANGUAGES = get_available_languages()

    if lang in MODELTRANS_AVAILABLE_LANGUAGES:
        return lang
    return get_default_language()


def split_translated_fieldname(field_name):
    _pos = field_name.rfind('_')
    return (field_name[0:_pos], field_name[_pos + 1:])


def build_localized_fieldname(field_name, lang):
    if lang == 'id':
        # The 2-letter Indonesian language code is problematic with the
        # current naming scheme as Django foreign keys also add "id" suffix.
        lang = 'ind'
    return str('{}_{}'.format(field_name, lang.replace('-', '_')))
