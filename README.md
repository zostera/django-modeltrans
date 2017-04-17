# django-modeltranslation2

# relevant 3rd party documentation
- [PostgreSQL jsonb functions](https://www.postgresql.org/docs/9.5/static/functions-json.html)

# Features

- Use one `JSONBField` for every record, rather than one field per language per translatable field.
- Django >= 1.11 for now
- PostgreSQL >= 9.4 and Psycopg2 >= 2.5.4.

# Running the tests

in `example` subdirectory, with the requirements in `requirements.txt`, use `PYTHONPATH=.. ./manage.py test`

# Attribution
Some concepts and code from https://github.com/deschler/django-modeltranslation,
which is in turn inspired by https://github.com/zmathew/django-linguo

We started this solution at Zostera because we did not like:
- The way django-modeltranslation adds one field per language (and thus requires a migration
when adding language)
- The unpredictability of the original field.
-
Since JSONB is supported by Postgres now, we developed this approach.
