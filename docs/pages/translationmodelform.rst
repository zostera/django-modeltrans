TranslationModelForm
==============

TranslationModelForm is an adaptation of Django's ModelForm that allow easy management of translation fields.
Assuming your Model has an i18n ModelTrans field, you can used TranslationModelForm to specify which translation fields
to include and for which languages.

For example, given a NewsRoom model::

    class NewsRoom(models.Model):
        name = models.CharField(max_length=255)
        text = models.CharField(max_length=255)
        default_language = models.CharField(max_length=2)

        i18n = TranslationField(fields=("name",), fallback_language_field="default_language")

You can define a TranslationModelForm as::

    from modeltrans.forms import TranslationModelForm

    class NewsRoomTranslationForm(TranslationModelForm):

        class Meta:
            fields = (name, text)
            included_languages = ["browser", "fr", "fallback"]
            fallback_language = "en"

This will define a form with maximally three language entries per field, say 'nl', 'fr' and 'en', where 'nl' is the
active browser language, and 'en' the defined fallback language. The exclude Meta options can also be used to define
fields are in the form, where the form field_order parameter can be used to define the field ordering.

included_languages
------------------

Defines the languages included in the form.
    - Options are:
        - "browser": the language that is active in the browser session
        - "fallback": the fallback language either define in the form, the model instance, or in the system, in that order of priority
        - a language code: e.g. "fr", "it"
    - Ordering: the ordering defined in the declaration is preserved
    - Overlap is removed, e.g. ["browser", "fr", "fallback"], becomes ["fr"] if all are equal.

Included_languages can be defined in the form Meta options as in the example above,
or as a form kwarg as in::

    form = NewsRoomTranslationForm(included_languages=["it", "fallback"])


fallback_language
-----------------
Defines the fallback_language in the form.
Requires "fallback" to be included in included_languages.
Can be defined via the form Meta options as in the example above,
and also be passed as a Kwarg like included_languages.
The following prioritization is followed:

    1) fallback_language passed as form parameter:
        Form(fallback_language="fr")
    2) the Meta option "fallback_language":
        e.g. Meta: fallback_language = "fr"
    3) a custom fallback of a model instance set via "fallback_language_field":
        e.g. i18n = TranslationField(fields=("title", "header"), fallback_language_field="language_code")
    4) The default language of the system. If not Meta option is given fallback reverts to get_default_language()

field properties
----------------
Properties of translation form fields are inherited from form field that is generated for the original model field.
The label of the field is adjusted to included that language and to designate the field as a translation or default
fallback field, as follows:
  - translation fields: "field name (NL, translation language)"

  - fallback field: "field name (EN, default language)"

future
------
The following features will be developed in future:
  1) Setting the default fallback field to "read only" in order to generate special forms for translator who should
     not change the fallback.

  2) Making the text of field labels customizable via form Meta options, as in "field name (NL {translation_language_string})"
     where translation_language_string is defined in Meta options as, e.g.: translation_language_string = _("translatable language")
