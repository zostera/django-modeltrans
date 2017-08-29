# django-modeltrans change log

## 0.0.6 (2017-08-29)
 - Also fall back to `DEFAULT_LANGUAGE` if the value for a key in the translations dict is falsy.

## 0.0.5 (2017-07-26)
 - Removed registration in favour of adding the `TranslationField` to a model you need to translated.
 - Created documentation.

## 0.0.4 (2017-05-19)
 - Improve robustness of rewriting lookups in QuerySets

## 0.0.3 (2017-05-18)
 - Add the `gin` index in the data migration.
 - Added tests for the migration procedure.
