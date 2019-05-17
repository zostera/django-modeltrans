Working with models recipes.
============================

Inheritance of translation models.
----------------------------------

In case when you are working with models Inheritance and you want to change
behavior of TranslationField declared in parent model, you should use
`i18n_field_params` attribute and declare there parameters
for child model field.

Example of use: ::

    class ParentModel(models.Model):
        info = models.CharField(max_length=255)

        i18n = TranslationField(fields=("info", ), required_languages=("en",))


    class ChildModel(ParentModel):
        child_info = models.CharField(max_length=255)

        i18n_field_params = {
            "fields": ("info", "child_info"),
            "required_languages": ("nl",)
        }
