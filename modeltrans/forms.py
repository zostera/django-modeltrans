import itertools

from django import forms
from django.utils.translation import gettext_lazy as _

from .conf import get_available_languages, get_default_language
from .fields import get_instance_field_value
from .translator import get_i18n_field
from .utils import build_localized_fieldname, get_language

# TODO FUTURE: will not be done at this stage:
# the "all" option to include all languages
# customizable translation and fallback field labels
# setting fallback to readonly


# TODO FUTURE INCLUDED_LANGUAGE_OPTIONS = ["all", "browser", "fallback"]  - will be done at a later stage
INCLUDED_LANGUAGE_OPTIONS = ["browser", "fallback"]


class TranslationModelFormOptions(forms.models.ModelFormOptions):
    """Add the translation form options to the Meta options."""

    def __init__(self, options=None):
        super().__init__(options)
        self.included_languages = getattr(options, "included_languages", ["browser"])
        # TODO FUTURE self.fallback_readonly = getattr(options, "fallback_readonly", True)
        self.fallback_language = getattr(options, "fallback_language", None)


class TranslationModelFormMetaClass(forms.models.ModelFormMetaclass):
    def __new__(mcs, name, bases, attrs):
        """
        Include all translation fields for translatable fields declared in the form.

        We use the standard ModelForm field declaration procedure of the ModelFormMetaClass,
        so that all fields are declared during creation of the new object.

        Different actions are required for different Meta class options:
        1) fields - if fields are declared explicitly with the fields option, the related i18n fields will not be
        included, and these have to be added to base_fields.
        2) exclude - if fields are declared implicitly with the exclude option, the i18n translation fields, as well as
        the i18n field itself, will be included. We will remove the i18n field.

        Here all languages are included, so that in the form we can curate which fields are available according to
        settings of the form instance (e.g. kwarg overrides, or model instance fallbacks).
        """
        new_class = super().__new__(mcs, name, bases, attrs)

        # from ModelFormMetaClass, needed for calling fields for model
        base_formfield_callback = None
        for b in bases:
            if hasattr(b, "Meta") and hasattr(b.Meta, "formfield_callback"):
                base_formfield_callback = b.Meta.formfield_callback
                break
        formfield_callback = attrs.pop("formfield_callback", base_formfield_callback)

        # get options, with extra translation form options
        opts = new_class._meta = TranslationModelFormOptions(getattr(new_class, "Meta", None))
        model_class = opts.model

        # TODO CHECK:
        # how does modeltrans add fields during exclude, normally? i.e. what determines the complete language list?
        included_languages = get_available_languages()

        # Note that base_fields generated by ModelForm do not yet include translation fields if generated with "fields"
        # Meta option, but includes all translation fields if generated with "excludes" Meta option.
        base_fields = list(new_class.base_fields.keys())

        # convert to list in case it is a tuple
        opts_fields = list(opts.fields) if opts.fields else None
        opts_exclude = list(opts.exclude) if opts.exclude else None

        if model_class:
            i18n_field = get_i18n_field(model_class)
            if i18n_field:

                for original_field_name in i18n_field.fields:  # for all translated fields

                    # for all possible system languages
                    for language in included_languages:
                        field_name = build_localized_fieldname(
                            original_field_name, language, ignore_default=True
                        )

                        # add i18n field if an explicitly chosen field
                        if (
                            opts.fields
                            and original_field_name in base_fields
                            and field_name not in base_fields
                        ):
                            base_fields.append(field_name)
                            opts_fields.append(field_name)

                        # remove field if an explicitly excluded field
                        if (
                            opts.exclude
                            and original_field_name in opts.exclude
                            and field_name in base_fields
                        ):
                            base_fields.remove(field_name)
                            opts_exclude.append(field_name)

                    # Remove the i18n field if present (e.g. because of using the exclude option)
                    name = f"{original_field_name}_i18n"
                    if name in base_fields:
                        base_fields.remove(name)
                    if opts.exclude:
                        opts_exclude.append(name)

                    # Remove the i18n field for the system default language, because that already exists as the default
                    name = f"{original_field_name}_{get_default_language()}"
                    if name in base_fields:
                        base_fields.remove(name)
                    if opts.fields and name in opts.fields:
                        opts_fields.remove(name)
                    if opts.exclude and name not in opts.exclude:
                        opts_exclude.append(name)

                opts.fields = opts_fields
                opts.exclude = opts_exclude

                base_fields = forms.fields_for_model(
                    opts.model,
                    opts.fields,
                    opts.exclude,
                    opts.widgets,
                    formfield_callback,
                    opts.localized_fields,
                    opts.labels,
                    opts.help_texts,
                    opts.error_messages,
                    opts.field_classes,
                    # limit_choices_to will be applied during ModelForm.__init__().
                    apply_limit_choices_to=False,
                )

                # Override default model fields with any custom declared ones
                # (plus, include all the other declared fields).
                base_fields.update(new_class.declared_fields)
            else:
                base_fields = new_class.declared_fields

            # override base_fields with properly determined set of all translation fields
            # based on ModelForm
            new_class.base_fields = base_fields

        return new_class


class TranslationModelForm(forms.ModelForm, metaclass=TranslationModelFormMetaClass):
    """
    ModelForm that adds fields for translations.

    Meta options and form parameters include:
    - included_languages: a list defining languages for which translation fields are added.
        - Options are:
            - "browser": current browser language
            - "fallback": the current fallback language, which is the system fallback,
                          or a customized fallback of the translation field.
            # TODO FUTURE - "all": all system languages are included
            - "fr": a language code
        - Overlap is removed, e.g. ["browser", "fr", "fallback"], becomes ["fr"] if all are equal.
        - The list order determines the order of fields in the form.
        - included languages can also be passed via form kwargs to customize on the fly, useful for
          generating translation forms for a specific language.
    - fallback_language: for adapting the fallback language specification on the fly and override the Meta option and/or
    model translation field custom fallback.
    # TODO FUTURE - fallback_readonly: boolean defining whether fallback fields are editable or only for reference.
    #  This is useful if editing fallback languages is to be restricted. Can be passed as kwarg too.
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
                included_languages = ["browser", "es", "fallback"]
                # TODO FUTURE later fallback_readonly = False


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
                included_languages=[translation_language_code, "fallback"],
                # TODO FUTURE fallback_readonly=True
            )
    """

    # TODO FUTURE fallback_readonly=None
    def __init__(self, *args, included_languages=None, fallback_language=None, **kwargs):
        """Prune the translation fields based on included languages and fallback_language."""

        self.model_i18n_field = get_i18n_field(self._meta.model)
        self.included_languages = included_languages or self._meta.included_languages
        self.i18n_fields = [
            field for field in self.model_i18n_field.fields if field in self.base_fields.keys()
        ]

        # NOTE: because we update opts.fields and opts.exclude in META, field initial values are set in ModelForm
        super().__init__(*args, **kwargs)

        # the following require the instance generated in the super call
        self.fallback_language = self.get_fallback_language(fallback_language)
        self.languages = self.get_languages()
        self.included_fields = self.included_fields()

        self.remove_excess_fields()
        self.set_included_field_properties()
        self.order_translation_fields()

    def included_fields(self):
        """Return a dictionary mapping original field names to a list of included translation field names."""

        field_dict = {}
        for original_field in self.i18n_fields:
            # list is created in order of languages
            field_dict[original_field] = [
                build_localized_fieldname(original_field, language, ignore_default=True)
                for language in self.languages
            ]
        field_dict["__all__"] = list(itertools.chain.from_iterable(field_dict.values()))
        return field_dict

    def set_included_field_properties(self):
        """Apply settings of all original field to relevant translation fields."""

        for original_field_name in self.i18n_fields:
            original_field = self.base_fields[original_field_name]
            for field_name in self.included_fields[original_field_name]:
                language = get_default_language()
                if field_name != original_field_name:
                    language = field_name.replace(f"{original_field_name}_", "")
                is_translation = language != self.fallback_language
                # TODO FUTURE idea to customize this text (in Meta), e.g. translation_label and fallback_label
                label_text = _("translation language") if is_translation else _("default language")
                label = f"{original_field.label} ({language.upper()}, {label_text})"
                self.fields[field_name].label = label
                self.fields[field_name].required = (
                    False if is_translation else original_field.required
                )
                self.fields[field_name].widget = original_field.widget

    def order_translation_fields(self):
        """
        Set the order of the fields, ideally replacing the original field with the set of fields in included fields.

        For the Meta 'excludes' option we do a cruder ordering where translated fields types are grouped,
        but the per type the languages are in order of: browser, other, fallback
        """

        # form parameter field_order takes priority, otherwise adopt order of fields in meta fields option, if available
        field_order = self.field_order or None
        if not field_order and self._meta.fields and self._meta.fields != "all":
            field_order = self._meta.fields

        # in case of an explicit field order replace original field with set of included fields
        if field_order:
            new_field_order = list(field_order)
            for original_field in self.i18n_fields:
                # TODO: what if it is not in the new_field_order?
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

        # get all the form fields related to the form i18n fields
        translation_fields = []
        for original_field_name in self.i18n_fields:
            translation_fields += [field for field in self.fields if original_field_name in field]

        excluded_fields = [
            field for field in translation_fields if field not in self.included_fields["__all__"]
        ]
        for field_name in excluded_fields:
            if field_name in self.fields:
                self.fields.pop(field_name)

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

        return get_default_language()  # TODO: should be use get_fallback_chain? based on language?

    def get_languages(self):
        """Get the languages based on options included in include languages, in the order they are submitted."""

        languages = []
        if self.included_languages:
            # TODO FUTURE later stage
            # if len(self.included_languages) > 1 and "all" in self.included_languages:
            #    raise ValueError("included languages: you cannot include other options when including 'all'")

            for value in self.included_languages:
                if not isinstance(value, str):
                    raise ValueError("included_languages: values should be strings")
                # TODO: need to consider what to do with en_GB style languages ...?
                if len(value) > 2 and value not in INCLUDED_LANGUAGE_OPTIONS:
                    raise ValueError(f"included_languages: value {value} is not permitted")
                if len(value) < 2:
                    raise ValueError(f"included_languages: value {value} is not permitted")
                if len(value) == 2 and value not in get_available_languages():
                    raise ValueError(
                        f"included_languages: {value} is not an available language in the system"
                    )

                if value == "browser":
                    languages.append(get_language())
                elif value == "fallback":
                    languages.append(self.fallback_language)
                # TODO FUTURE at later stage
                # elif value == "all":
                #    languages = get_available_languages()
                else:
                    languages.append(
                        value
                    )  # assuming above checks assure this is an existing language in the system

        if not languages:
            raise ValueError("included_languages: Error. No languages have been defined.")

        # remove duplicates while preserving the order
        no_repeats = set()
        return [x for x in languages if x not in no_repeats and not no_repeats.add(x)]
