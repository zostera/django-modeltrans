Translations in forms
=====================

`TranslationModelForm` is an adaptation of Django's `django.forms.ModelForm` that allows management of translation fields.
Assuming your model is translated with modeltrans,
you can use `TranslationModelForm` to specify which languages to include form fields for.

For example, given a `NewsRoom` model::

    class NewsRoom(models.Model):
        name = models.CharField(max_length=255)
        text = models.CharField(max_length=255)
        default_language = models.CharField(max_length=2)

        i18n = TranslationField(fields=("name", "text"), fallback_language_field="default_language")

You can define a form using `TranslationModelForm` as::

    from modeltrans.forms import TranslationModelForm

    class NewsRoomTranslationForm(TranslationModelForm):

        class Meta:
            fields = ("name", "text")
            languages = ["browser", "fr", "fallback"]
            fallback_language = "en"

This defines a form with at most three language inputs per field, say `"nl"`, `"fr"` and `"en"`,
where `"nl"` is the active browser language, and `"en"` the defined fallback language.
`Meta.exclude` can also be used to define which fields are in the form,
where the forms' `field_order` parameter can be used to define the field ordering.

Setting the form languages
--------------------------

`languages` defines the languages included in the form.
    - Options are:
        - `"browser"`: the language that is active in the browser session
        - `"fallback"`: the fallback language either defined in the form, the model instance, or in the system, in that order of priority
        - a language code: e.g. `"fr"`, `"it"`
    - Default: `["browser", "fallback"]`
    - Ordering: the ordering defined in the declaration is preserved
    - Duplicate languages are removed, e.g. `["browser", "fr", "fallback"]`, becomes `["fr"]` if browser language and fallback are also `"fr"`.

`languages` can be defined in the form `Meta` options as in the example above, or as a form kwarg as in::

    form = NewsRoomTranslationForm(languages=["it", "fallback"])


Setting the fallback language
-----------------------------

`fallback_language` defines the fallback language in the form.
Requires `"fallback"` to be included in `languages`.
Can be defined via the form `Meta` options as in the example above, and also be passed as a kwarg like `languages`.
The following prioritization is followed:

    1) `fallback_language` passed as form parameter:
        `Form(fallback_language="fr")`
    2) the `Meta` option `fallback_language`:
        e.g. `class Meta: fallback_language = "fr"`
    3) A custom fallback of a model instance set via `fallback_language_field`:
        e.g. `i18n = TranslationField(fields=("title", "header"), fallback_language_field="language_code")`
    4) The default language of the system: If no `Meta` option is given fallback reverts to `get_default_language()`

Handling of field properties
----------------------------

Properties of translation form fields are inherited from the form field that is generated for the original model field.
The label of the field is adjusted to include the relevant language
and to designate the field as a translation or default fallback field, as follows:

  - translation fields: "field name (NL, translation language)"
  - fallback field: "field name (EN, fallback language)"

The labels "translation language" and "fallback language" are customizable using the `Meta` options:

  - `fallback_label` (defaults to "fallback language")
  - `translation_label` (defaults to "translation language")
