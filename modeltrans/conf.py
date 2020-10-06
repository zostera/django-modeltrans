import itertools

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_modeltrans_setting(key):
    modeltrans_settings = {
        "MODELTRANS_AVAILABLE_LANGUAGES": get_available_languages(),
        "MODELTRANS_FALLBACK": getattr(
            settings, "MODELTRANS_FALLBACK", {"default": (get_default_language(),)}
        ),
        "MODELTRANS_ADD_FIELD_HELP_TEXT": getattr(settings, "MODELTRANS_ADD_FIELD_HELP_TEXT", True),
    }
    return modeltrans_settings.get(key)


def get_default_language():
    return settings.LANGUAGE_CODE


def get_available_languages_setting():
    """
    list of available languages for modeltrans translations.
    defaults to the list of language codes extracted from django setting LANGUAGES
    """
    languages = tuple(
        set(
            getattr(
                settings,
                "MODELTRANS_AVAILABLE_LANGUAGES",
                (code for code, _ in getattr(settings, "LANGUAGES")),
            )
        )
    )

    if not all(isinstance(x, str) for x in languages):
        raise ImproperlyConfigured(
            "MODELTRANS_AVAILABLE_LANGUAGES should be an iterable of strings"
        )

    # make sure LANGUAGE_CODE is not in available languages
    return (lang for lang in languages if lang != get_default_language())


def get_available_languages(include_default=True):
    """
    Returns a tuple of available languages for django-modeltrans.
    """
    MODELTRANS_AVAILABLE_LANGUAGES = get_available_languages_setting()

    if include_default:
        return tuple(
            set(itertools.chain(MODELTRANS_AVAILABLE_LANGUAGES, (get_default_language(),)))
        )
    else:
        return MODELTRANS_AVAILABLE_LANGUAGES


def check_fallback_chain():
    MODELTRANS_FALLBACK = get_modeltrans_setting("MODELTRANS_FALLBACK")
    MODELTRANS_AVAILABLE_LANGUAGES = get_available_languages(include_default=True)

    if "default" not in MODELTRANS_FALLBACK:
        raise ImproperlyConfigured("MODELTRANS_FALLBACK setting must have a `default` key.")

    message_fmt = (
        "MODELTRANS_FALLBACK contains language `{}` "
        "which is not in MODELTRANS_AVAILABLE_LANGUAGES"
    )
    for lang, chain in MODELTRANS_FALLBACK.items():
        if lang != "default" and lang not in MODELTRANS_AVAILABLE_LANGUAGES:
            raise ImproperlyConfigured(message_fmt.format(lang))
        for lang in chain:
            if lang not in MODELTRANS_AVAILABLE_LANGUAGES:
                raise ImproperlyConfigured(message_fmt.format(lang))


def get_fallback_chain(lang):
    """
    Returns the list of fallback languages for language `lang`.

    For example, this function will return `('nl', 'en')` when called
    with `lang='fy'` and configured like this::

        LANGUAGE_CODE = 'en'

        MODELTRANS_FALLBACK = {
           'default': (LANGUAGE_CODE, ),
           'fy': ('nl', 'en')
        }
    """
    MODELTRANS_FALLBACK = get_modeltrans_setting("MODELTRANS_FALLBACK")

    if lang not in MODELTRANS_FALLBACK.keys():
        lang = "default"

    return MODELTRANS_FALLBACK[lang]
