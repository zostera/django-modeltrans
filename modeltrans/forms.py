import itertools

from django import forms
from django.utils.translation import gettext

from .conf import get_available_languages, get_default_language
from .fields import get_instance_field_value
from .translator import get_i18n_field
from .utils import build_localized_fieldname, get_language

LANGUAGE_OPTIONS = ["browser", "fallback"]


class TranslationModelFormMetaClass(forms.models.ModelFormMetaclass):
    def __new__(mcs, name, bases, attrs):
        """
        Include all translation fields for translatable fields declared in the form.

        The fields and exclude Meta options are extended before the standard ModelFormMetaClass creates the
        form fields, so that the form fields are only created once:
        1) fields - if fields are declared explicitly with the fields option, the related i18n fields will not be
        included, and these are added to fields.
        2) exclude - if fields are declared implicitly with the exclude option (or fields = "__all__"), the i18n
        translation fields, as well as the i18n field itself, will be included. The i18n field and the translation
        fields of excluded fields are added to exclude.

        Here all languages are included, so that in the form we can curate which fields are available according to
        settings of the form instance (e.g. kwarg overrides, or model instance fallbacks).
        """
        meta = attrs.get("Meta")
        inherits_meta = meta is None
        if inherits_meta:
            meta = next((base.Meta for base in bases if hasattr(base, "Meta")), None)

        model_class = getattr(meta, "model", None)
        if model_class and (i18n_field := get_i18n_field(model_class)):
            # Like DeclarativeFieldsMetaclass: the fields declared on the bases and on this class,
            # except fields removed by setting them to None.
            declared_fields = set()
            for base in bases:
                declared_fields.update(getattr(base, "declared_fields", {}))
            for key, value in attrs.items():
                if isinstance(value, forms.Field):
                    declared_fields.add(key)
                elif value is None:
                    declared_fields.discard(key)

            fields, exclude = mcs.get_translation_fields_and_exclude(
                i18n_field,
                getattr(meta, "fields", None),
                getattr(meta, "exclude", None),
                declared_fields,
            )
            meta_attrs = {
                "__module__": meta.__module__,
                "__qualname__": meta.__qualname__,
                "fields": fields,
                "exclude": exclude,
            }
            attrs["Meta"] = type("Meta", (meta,), meta_attrs)

        new_class = super().__new__(mcs, name, bases, attrs)

        # Add the translation form options to the options created by ModelFormMetaclass.
        new_class._meta.languages = getattr(meta, "languages", LANGUAGE_OPTIONS)
        new_class._meta.fallback_language = getattr(meta, "fallback_language", None)

        # Restore the original Meta, so subclasses extend the Meta options as defined,
        # rather than the options already extended with translation fields.
        if not inherits_meta:
            new_class.Meta = meta
        elif "Meta" in vars(new_class):
            del new_class.Meta

        return new_class

    @staticmethod
    def get_translation_fields_and_exclude(i18n_field, fields, exclude, declared_fields):
        """Return the fields and exclude Meta options, extended with the translation fields."""
        default_language = get_default_language()
        languages = get_available_languages()

        if fields is not None and fields != forms.models.ALL_FIELDS:
            fields = list(fields)
            for original_field_name in i18n_field.fields:
                # add translation fields for an explicitly chosen field
                if original_field_name in fields or original_field_name in declared_fields:
                    for language in languages:
                        field_name = build_localized_fieldname(
                            original_field_name, language, ignore_default=True
                        )
                        if field_name != original_field_name and field_name not in fields:
                            fields.append(field_name)

                # Remove the translation field for the system default language, because that already exists
                # as the original field.
                name = f"{original_field_name}_{default_language}"
                if name in fields:
                    fields.remove(name)

        if exclude is not None or fields == forms.models.ALL_FIELDS:
            exclude = list(exclude or [])
            for original_field_name in i18n_field.fields:
                # exclude translation fields of an explicitly excluded field
                if original_field_name in exclude:
                    for language in languages:
                        field_name = build_localized_fieldname(
                            original_field_name, language, ignore_default=True
                        )
                        if field_name not in exclude:
                            exclude.append(field_name)

                # Exclude the i18n field and the translation field for the system default language, because that
                # already exists as the original field.
                for name in (
                    f"{original_field_name}_i18n",
                    f"{original_field_name}_{default_language}",
                ):
                    if name not in exclude:
                        exclude.append(name)

        return fields, exclude


class TranslationModelForm(forms.ModelForm, metaclass=TranslationModelFormMetaClass):
    """
    Model form that only adds translation fields for specified languages.

    Meta options and form parameters include:
    - languages: a list defining languages for which translation fields are added.
        - Options are:
            - "browser": current browser language
            - "fallback": the current fallback language, which is the system fallback,
                          or a customized fallback of the translation field.
            - "fr": a language code
        - Overlap is removed, e.g. ["browser", "fr", "fallback"], becomes ["fr"] if all are equal.
        - The list order determines the order of fields in the form.
        - included languages can also be passed via form kwargs to customize on the fly, useful for
          generating translation forms for a specific language.
    - fallback_language: for adapting the fallback language specification on the fly and override the Meta option and/or
    model translation field custom fallback.

    Form parameters take priority of Meta options.

    For the fallback language the following priority holds:
    1) fallback_language passed as form parameter: Form(fallback_language="fr")
    2) the Meta option "fallback_language":
        e.g. Meta:
                fallback_language = "fr"
    3) a custom fallback of a model instance set via "fallback_language_field":
        e.g. i18n = TranslationField(fields=("title", "header"), fallback_language_field="language_code")
    4) The default language of the system. If not Meta option is given fallback reverts to get_default_language()

    Code example:
        class ChallengeModel(models.Model):
            language_code = CharField()
            title = CharField()
            description = CharField()
            i18n = TranslationField(fields=("title", "description"), fallback_language_field="language_code")


        class ChallengeModelForm(RefactoredModelTransForm):

            class Meta:
                fields = ["title", "description"] or exclude = ["language_code"]
                languages = ["browser", "es", "fallback"]


        class ChallengeCreateUpdateView(GenericCreateUpdateView):
            '''An update view with a browser language, spanish and browser field for translations.'''
            model = Challenge
            form_class = ChallengeModelForm()


        class ChallengeTranslationView(GenericCreateUpdateView):
            '''
            A translation view with a specific translation language field and non-editable fallback field as reference.
            '''
            model = Challenge
            form_class = ChallengeModelForm(
                languages=[translation_language_code, "fallback"],
            )
    """

    def __init__(self, *args, languages=None, fallback_language=None, **kwargs):
        """Prune the translation fields based on included languages and fallback_language."""

        self.model_i18n_field = get_i18n_field(self._meta.model)
        self.languages = languages or self._meta.languages
        self.i18n_fields = [
            field for field in self.model_i18n_field.fields if field in self.base_fields.keys()
        ]

        # Given that we set opt.fields and opts.exclude in Meta,
        # the setting of initial values that occurs in ModelForm includes
        # any additional translation fields that have been added in Meta.
        super().__init__(*args, **kwargs)

        # the following require the instance generated in the super call
        self.fallback_language = self.get_fallback_language(fallback_language)
        self.language_codes = self.get_language_codes()
        self.included_fields = self.get_included_fields()

        self.remove_excess_fields()
        self.set_translation_field_attributes()
        self.order_translation_fields()

    def get_included_fields(self):
        """
        Return a dictionary mapping original field names to a list of included field names,
        which may or may not include the original field name.
        """

        fields = {}
        for original_field in self.i18n_fields:
            fields[original_field] = [
                build_localized_fieldname(original_field, language_code, ignore_default=True)
                for language_code in self.language_codes
            ]
        fields["__all__"] = list(itertools.chain.from_iterable(fields.values()))
        return fields

    def set_translation_field_attributes(self):
        """Apply settings of all original field to relevant translation fields."""

        for original_field_name in self.i18n_fields:
            original_field = self.base_fields[original_field_name]
            for field_name in self.included_fields[original_field_name]:
                language = get_default_language()
                if field_name != original_field_name:
                    language = field_name.replace(f"{original_field_name}_", "")
                is_translation = language != self.fallback_language
                label_text = (
                    gettext("translation language")
                    if is_translation
                    else gettext("default language")
                )
                label = f"{original_field.label} ({language.upper()}, {label_text})"
                self.fields[field_name].label = label
                self.fields[field_name].required = (
                    False if is_translation else original_field.required
                )
                self.fields[field_name].widget = original_field.widget

    def order_translation_fields(self):
        """
        Set the order of the fields, ideally replacing the original field with the set of fields in included fields.

        For the Meta.excludes use a cruder ordering where translated fields types are grouped,
        but per type the languages are in order of: browser, other, fallback
        """

        # Form parameter field_order takes priority, otherwise adopt order of fields in Meta fields option, if available
        field_order = self.field_order or None
        if not field_order and self._meta.fields:
            field_order = self._meta.fields

        # in case of an explicit field order replace original field with set of included fields
        if field_order:
            new_field_order = list(field_order)
            for original_field in self.i18n_fields:
                if original_field in new_field_order:
                    index = new_field_order.index(original_field) + 1
                    new_field_order[index:index] = self.included_fields[original_field]
                    new_field_order.pop(index - 1)
            field_order = new_field_order
        else:
            # if no explicit field order adopt the order of i18n form fields used to generate the included fields
            field_order = self.included_fields["__all__"]

        self.order_fields(field_order)

    def remove_excess_fields(self):
        """Remove translations fields that are not included in languages."""
        fields = self.fields.copy()
        for original_field_name in self.i18n_fields:
            for field in fields:
                if original_field_name in field and field not in self.included_fields["__all__"]:
                    self.fields.pop(field)

    def get_fallback_language(self, fallback_language=None):
        """
        Get the fallback language.

        Priority is defined as:
        1) key word argument
        2) form Meta option
        3) model instance custom fallback
        4) system default fallback
        """
        if fallback_language:
            return fallback_language

        if self._meta.fallback_language:
            return self._meta.fallback_language

        if self.model_i18n_field.fallback_language_field and self.instance.pk:
            return get_instance_field_value(
                self.instance, self.model_i18n_field.fallback_language_field
            )

        return get_default_language()

    def get_language_codes(self):
        """Get the languages based on options included in include languages, in the order they are submitted."""

        valid_languages = get_available_languages()
        languages = []
        if self.languages:
            for value in self.languages:
                if value == "browser":
                    value = get_language()
                elif value == "fallback":
                    value = self.fallback_language
                if value not in valid_languages:
                    raise ValueError(f"languages: value {value} is not permitted")
                languages.append(value)

        if not languages:
            raise ValueError("languages: No languages have been defined.")

        # remove duplicates while preserving the order
        no_repeats = set()
        return [x for x in languages if x not in no_repeats and not no_repeats.add(x)]
