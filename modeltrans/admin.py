from .conf import get_default_language
from .translator import get_i18n_field
from .utils import get_language


class ActiveLanguageMixin(object):
    """
    Add this mixin to your admin class to exclude all virtual fields, except:

     - The original field (for the default language, settings.LANGUAGE_CODE)
     - The field for the currently active language, without fallback.
    """

    def get_exclude(self, request, obj=None):
        i18n_field = get_i18n_field(self.model)
        # use default implementation for models without i18n-field
        if i18n_field is None:
            return super().get_exclude(request)

        language = get_language()
        if language == get_default_language():
            language = False

        excludes = []
        for field in i18n_field.get_translated_fields():
            # Not excluded:
            # - language is None: the _i18n-version of the field.
            # - language equals the current language
            if field.language == language:
                continue

            excludes.append(field.name)

        # de-duplicate
        return list(set(excludes))
