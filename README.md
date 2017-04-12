# django-model-translation2

source of the `order_by` error message:

https://github.com/django/django/blob/19b8ca5824b63ba1b46a2c12ccb67af920c5b685/django/db/models/sql/query.py#L1364


# relevant 3rd party documentation
- [PostgreSQL jsonb functions](https://www.postgresql.org/docs/9.5/static/functions-json.html)

# Features

- Use one `JSONBField` for every record, rather than one field per language per translatable field.
- Django >= 1.11 for now
- PostgreSQL >= 9.4 and Psycopg2 >= 2.5.4.


# Attribution
Lots of concepts and code from https://github.com/deschler/django-modeltranslation,
which is in turn inspired by https://github.com/zmathew/django-linguo

We started this solution at Zostera because we did not like the way
django-modeltranslation adds one field per language and thus requires a migration
when adding language and the unpredictability of the original field.
Since JSONB is supported by Postgres now, we developed this approach.
