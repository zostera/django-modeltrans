from .conf import get_default_language
from .translator import get_i18n_field
from .utils import get_language


class ActiveLanguageMixin(object):
    '''
    Add this mixin to your admin class to hide the untranslated field and all
    translated fields, except:

     - The field for the default language (settings.LANGUAGE_CODE)
     - The field for the currently active language.
    '''
    def get_exclude(self, request, obj=None):
        # use default implementation for models without i18n-field
        i18n_field = get_i18n_field(self.model)
        if i18n_field is None:
            return super(ActiveLanguageMixin, self).get_exclude(request)

        language = get_language()
        if language == get_default_language():
            language = False

        excludes = []
        for field in i18n_field.get_translated_fields():
            if field.language is None or field.language == language:
                continue
            excludes.append(field.name)

            # also add the name of the original field, as it is added
            excludes.append(field.original_field.name)

        # de-duplicate
        return list(set(excludes))
