django-modeltrans change log
============================

## 0.5.2 (and 0.5.2) (2021-01-12)
 - Adjust imports to remove deprecation warnings with django==3.1.* #65

## 0.5.0 (2020-11-23)
 - Add per-record fallback feature #63

## 0.4.0 (2019-11-22)
 - Drop python 2, Django 1.11 and Django 2.0 support #56
 - Add option for `i18n` model fields inheritance #51
 - Fix patching managers of models inheriting from an abstract models #50

## 0.3.4 (2019-01-15)
 - Fix exception on nullable i18n field #49

## 0.3.3 (2018-07-19)
 - Add instruction to remove `virtual_fields=True` to migration guide, fixes #45
 - Use `AppConfig` to compute path to app dir, fixes #46
 - Do not copy empty fields into i18n field, fixes #47

## 0.3.2 (2018-07-18)
 - Removed `encoding` kwarg to `open()` in `setup.py` to fix python 2.7 install.

## 0.3.1 (2018-07-16)
 - Added `long_description` to `setup.py`, no functional changes.

## 0.3.0 (2018-07-15)
 - Adopted [black](https://github.com/ambv/black) code style.
 - Removed auto-adding indexes, as it was unpredictable. You must add the `GinIndex` manually like described in the documentation on performance.
 - Support dict for `required_languages` argument to `TranslationField`, to allow more fine-grained mapping of field names to required languages.
 - `ActiveLanguageMixin` does not use the `<field>_i18n` version of the field, but rather the virtual field with the current active language. This makes sure no fallback values are accidentally saved for another language.


## 0.2.2 (2018-03-13)
 - Hide original field with `ActiveLanguageMixin`.
 - Raise an `ValueError` on accessing translated fields on a model fetched with `.defer('i18n')`.
 - do not accidentally add `i18n` to __dict__ in Model.create
 - Improve handling of explicit PK's and expression rewriting code.
 - Add help_text to virtual fields with language=None.

## 0.2.1 (2018-01-24)
 - Dropped support for Django 1.9 and 1.10.
 - Used `ugettext_lazy` rather than `ugettext` to fix admin header translation [#32](https://github.com/zostera/django-modeltrans/pull/32)
 - Removed default value `False` for `Field.editable`, to allow using the translated version of a field in a `ModelForm`.

## 0.2.0 (2017-11-13)
 - No annotations are made while ordering anymore, instead, expressions are passed onto the original `order_by()` method.
 - Any translated fields used in `Model.Meta.ordering` is transformed into the correct expression with django 2.0 and later (fixes #25).
 - `django.contrib.postgres.GinIndex` is added to the `i18n` column if it's supported by the django version used (1.11 and later). It can be disabled with the setting `MODELTRANS_CREATE_GIN`.
 - The migration generated from `./manage.py i18n_makemigrations <app>` used to move the data and add a GIN index. This is split into two commands: `./manage.py i18n_makemigrations` and `./manage.py i18n_make_indexes`.
 - Added support for `values(**expressions)`` with references to translated fields.
 - Added support for translated values in `annotate()`

## 0.1.2 (2017-10-23)
 - Ensure a dynamic mixed `MultilingualQuerySet` can be pickled.
 - Add basic support for `Func` in `order_by()`

## 0.1.1 (2017-10-23)
 - Allow adding `MultilingualManager()` as a manager to objects without translations to allow lookups
   of translated content through those managers.

## 0.1.0 (2017-10-23)
 - Use proper alias in subqueries, fixes #23.
 - Support lookups on and ordering by related translated fields (`.filter(category__name_nl='Vogels')`), fixes #13.
 - Use `KeyTextTransform()` rather than `RawSQL()` to access keys in the `JSONField`. For Django 1.9 and 1.10 the Django 1.11 version is used.

## 0.0.8 (2017-10-19)
 - Check if `MODELTRANS_AVAILABLE_LANGUAGES` only contains strings.
 - Make sure `settings.LANGUAGE_CODE` is never returned from `conf.get_available_languages()`

## 0.0.7 (2017-09-04)
 - Cleaned up the settings used by django-modeltrans [#19](https://github.com/zostera/django-modeltrans/pull/19).
   This might be a breaking change, depending on your configuration.

   - `AVAILABLE_LANGUAGES` is now renamed to `MODELTRANS_AVAILABLE_LANGUAGES` and defaults to the language codes in the
      django `LANGUAGES` setting.
   - `DEFAULT_LANGUAGE` is removed, instead, django-modeltrans uses the django `LANGUAGE_CODE` setting.
 - Added per-language configurable fallback using the `MODELTRANS_FALLBACK` setting.

## 0.0.6 (2017-08-29)
 - Also fall back to `DEFAULT_LANGUAGE` if the value for a key in the translations dict is falsy.

## 0.0.5 (2017-07-26)
 - Removed registration in favor of adding the `TranslationField` to a model you need to translated.
 - Created documentation.

## 0.0.4 (2017-05-19)
 - Improve robustness of rewriting lookups in QuerySets

## 0.0.3 (2017-05-18)
 - Add the `gin` index in the data migration.
 - Added tests for the migration procedure.
