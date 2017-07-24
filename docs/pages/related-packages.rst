Related packages
================

`django-modeltranslation <https://github.com/deschler/django-modeltranslation>`_
--------------------------------------------------------------------------------

Uses one field for each language/field combination, so having 3 languages and 3
translatable fields will result in 9 extra fields on each database table.
It rewrites queries in order to return the current language, but the
`contents of the original field are undetermined <http://django-modeltranslation.readthedocs.io/en/latest/usage.html#the-state-of-the-original-field>`_
if a field is translated.

`django-nence <https://github.com/tatterdemalion/django-nece/>`_
----------------------------------------------------------------

Also uses a `jsonb` PostgreSQL field, but has a bunch of custom `QuerySet` and `Model`
methods to get translated values.
It also requires one to inherit from a `TranslationModel`.

`django-i18nfield <https://github.com/raphaelm/django-i18nfield>`_
------------------------------------------------------------------

Stores JSON in a `TextField`, so does not allow lookup, searching or ordering by the translated fields.
