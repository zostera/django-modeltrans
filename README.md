# django-modeltrans

Translates Django models in a `JSONField` using a registration approach.

# Features

- Use one `django.contrib.postgres.JSONField` (PostgreSQL jsonb field) for every record, rather than one field per language per translatable field.
- Django 1.9, 1.10, 1.11 for now
- PostgreSQL >= 9.4 and Psycopg2 >= 2.5.4.

# Running the tests

`tox`

Running the tests without tox, `make test`

# Attribution
Some concepts and code from https://github.com/deschler/django-modeltranslation,
which is in turn inspired by https://github.com/zmathew/django-linguo

We started this solution at Zostera because we did not like:
- The way django-modeltranslation adds one field per language (and thus requires a migration
when adding language)
- The unpredictability of the original field.

Since JSONB is supported by Postgres now, we developed this approach.

# alternatives
- [django-nence](https://github.com/tatterdemalion/django-nece/)
  Also uses a `jsonb` PostgreSQL field, but has a bunch of custom `QuerySet` and `Model` methods to get translated values. It also requires one to inherit from a `TranslationModel`.
- [django-i18nfield](https://github.com/raphaelm/django-i18nfield)
  Stores JSON in a `TextField`, so does not allow lookup, searching or ordering by the translated fields.

# relevant 3rd party documentation
- [PostgreSQL jsonb functions](https://www.postgresql.org/docs/9.5/static/functions-json.html)
