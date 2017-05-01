# django-modeltrans

Translates Django models in a `JSONField` using a registration approach.

# Features

- Use one `django.contrib.postgres.JSONField` (PostgreSQL jsonb field) for every record, rather than one field per language per translatable field.
- Django 1.9, 1.10, 1.11 for now
- PostgreSQL >= 9.4 and Psycopg2 >= 2.5.4.

# Usage

 - Add `'modeltrans'` your `INSTALLED_APPS`.
 - Add a list of available languages to your `settings.py`:
   `AVAILABLE_LANGUAGES = ('en', 'nl', 'de', 'fr')`
 - Add a `translation.py` in each app you want to translate models for.
 - For each model you want to translate, create a `TransltionOptions` object:
```python
# models.py
from django.db import models


class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(null=True)

# translation.py
from modeltrans.translator import TranslationOptions, translator

from .models import Blog, Category


class BlogTranslationOptions(TranslationOptions):
    fields = ('title', 'body')

translator.register(Blog, BlogTranslationOptions)
```
 - Run `./manage.py makemigrations` to add the `i18n` JSONField to each model containing
   translations.
 - Each method now has some extra virtual fields. In the example above:
   - `title_nl`, `title_de`, ... allow getting/setting the specific languages
   - `title_i18n` follows the currently active translation in Django, and falls
     back to the default language:

```python
>>> b = Blog.objects.create(title='Falcon', title_nl='Valk')
>>> b.title
'Falcon'
>>> b.title_nl
'Valk'
>>> b.title_i18n
'Falcon'
>>> from django.utils.translation import override
>>> with override('nl'):
...   b.title_i18n
...
'Valk'
```

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
