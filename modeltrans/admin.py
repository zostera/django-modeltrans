from .conf import get_default_language
from .fields import TranslatedVirtualField
from .translator import get_i18n_field
from .utils import get_language


class ActiveLanguageMixin:
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


class TabbedLanguageMixin:
    """
    Mixin for your ModelAdmin to show a tabbed interface for i18n fields.

    """

    class Media:
        css = {
            "all": ("modeltrans/css/i18n_tabs.css",),
        }
        js = ("modeltrans/js/i18n_tabs.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i18n_field = get_i18n_field(self.model)

    def formfield_for_dbfield(self, db_field, request=None, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if self.i18n_field is None:
            return field

        if isinstance(db_field, TranslatedVirtualField):
            field.widget.attrs["data-i18n-lang"] = db_field.language or ""
            field.widget.attrs["data-i18n-field"] = db_field.original_name
            if not db_field.language:
                field.widget.attrs["required"] = not db_field.original_field.blank
            elif db_field.language == get_default_language():
                field.widget.attrs["data-i18n-default"] = "true"

        return field

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        if self.i18n_field is None or not fieldsets:
            return fieldsets

        fieldsets = list(fieldsets)

        real_to_virtual_fields = {}
        virtual_field_names = set()
        for field in self.i18n_field.get_translated_fields():
            virtual_field_names.add(field.name)

            # Remove _i18n fields from fieldsets
            if field.language is None:
                continue

            if field.original_name not in real_to_virtual_fields:
                real_to_virtual_fields[field.original_name] = []
            real_to_virtual_fields[field.original_name].append(field.name)

        translated_fieldsets = []
        for label, fieldset in fieldsets:
            field_names = []
            for field_name in fieldset.get("fields", []):
                if field_name in real_to_virtual_fields:
                    field_names.append([field_name] + sorted(real_to_virtual_fields[field_name]))

                elif field_name not in virtual_field_names:
                    field_names.append(field_name)

            new_fieldset = {
                "fields": field_names,
                "classes": fieldset.get("classes", []),
            }
            translated_fieldsets.append((label, new_fieldset))

        return translated_fieldsets
