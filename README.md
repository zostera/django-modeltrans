# django-modeltrans

[![Travis CI](https://travis-ci.org/zostera/django-modeltrans.svg?branch=master)](https://travis-ci.org/zostera/django-modeltrans)
[![Documentation Status](https://readthedocs.org/projects/django-modeltrans/badge/?version=latest)](http://django-modeltrans.readthedocs.io/en/latest/?badge=latest)


Translates Django model fields in a `JSONField` using a registration approach.

# Features/requirements

- Uses one `django.contrib.postgres.JSONField` (PostgreSQL jsonb field) per model.
- Django 1.9, 1.10, 1.11 (with their supported python versions)
- PostgreSQL >= 9.4 and Psycopg2 >= 2.5.4.
- [Available on pypi](https://pypi.python.org/pypi/django-modeltrans)
- [Documentation](http://django-modeltrans.readthedocs.io/en/latest/)

# Known issues

Below is a list of things not yet implemented/catched into the
Queryset/Manager and most of them can be considered TODO.

- If the field `'i18n'` is added to `.defer()`, augmentation will likely not work at all. Adding translated fields (`title_nl`) to `.defer()` will likely yield error messages, and doesn't make sense as they are stored in `i18n`.
- Using translated fields in `.distinct()`, `.extra()`, `.aggregate()`, `.update()` is not supported.
- Behaviour is tested using `CharField()` en `TextField()`, as these make most sense for translated values.
- Any ordering using `i18n`-fields defined in `Model.Meta.ordering` is only translated in django 2.0 and later ([django/django#8473](https://github.com/django/django/pull/8673) is required).

# Running the tests

`tox`

Running the tests only for the current environment, use `make test`

# Attribution

Some concepts and code come from https://github.com/deschler/django-modeltranslation,
which is in turn inspired by https://github.com/zmathew/django-linguo

We started this solution at Zostera because we did not like:
 - The way django-modeltranslation adds one field per language (and thus requires a migration
when adding a language);
 - The unpredictability of the original field.

Since JSONB is supported by Postgres now, we developed this approach.

# Relevant 3rd party documentation

- [PostgreSQL jsonb functions](https://www.postgresql.org/docs/9.5/static/functions-json.html)
