import hashlib

from django.utils.encoding import force_bytes
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


def _hash_generator(*args):
    '''
    Generate a 32-bit digest of a set of arguments that can be used to
    shorten identifying names.

    implementation form django.db.models.indexes
    '''
    h = hashlib.md5()
    for arg in args:
        h.update(force_bytes(arg))
    return h.hexdigest()[:6]


def get_i18n_index_name(Model):
    '''
    Returns the name for the gin index on the i18n field.

    Limited to 30 charachters because Django doesn't allow longer names.
    '''
    prefix = Model._meta.db_table
    if len(prefix) > 20:
        prefix = '{}_{}'.format(Model._meta.app_label[:14], _hash_generator(prefix))

    return '{}_i18n_gin'.format(prefix)
