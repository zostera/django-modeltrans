 # django-modeltrans TODO

 - [x] Verify that null by default is ok.
 - [x] POC working in an example project
  - [x] Filtering/excluding
  - [x] Ordering
  - [x] Fallback to base language while ordering
  - [x] `Model.objects.get()``

 - [ ] Building a package django-modeltrans on the POC
  - [x] read translatable fields from `TranslationOptions`, not from the model
        attribute.
  - [ ] filtering spanning relations
        `Category.objects.filter(blog__title_nl__contains='al')`

  - [x] create(title='...', title_nl='...'),
  - [x] and Model(title_nl='')
        Allow calling `create(title_nl='...')` and `Model(title_nl='...').save()`
        with translated versions of a field and make sure they arrive in the
        `i18n` field.
  - [x] assigning to translated fields: `m = Model(...), m.title_nl = 'foo', m.save()`
  - [ ] rewrite fieldnames in `F` expressions (https://github.com/deschler/django-modeltranslation/blob/master/modeltranslation/manager.py#L314)
  - [x] rewrite fieldnames in `Q` objects
  - [ ] deferred fields `defer()`, `only()`
  - [x] clean() and requiredness of translated fields.
  - [ ] values()
  - [ ] values_list()
  - [ ] select_related()
  - [x] Getting translated fields on a Model instance (if not annotated) (inject a __getattr__ on a Model?)
  - [x] Registration of translatable models and fields
    - [x] Remove the need of manually adding the `Manager` to the objects attribute
    - [x] inject the `i18n` field in the models.
    - [x] inject `__getattr__` to allow access to the translated fields
  - [ ] Tests
    - [x] Test suite runnable using `tox`.
    - [x] Test suite runnable in travisci
  - [x] ModelForm integration
  - [x] Django admin integration
  - [ ] Migration from django-model-translation
      - [ ] copy values from existing fields into the `i18n` field
      - [ ] move the value of `<original_field>_<DEFAULT_LANG>` to `<original_field>`
      - [ ] remove the `<original_field>_<lang>` fields
  - [ ] Documentation

# usage of managers/models in code

- [x] have a `title_i18n` field to get the translated version for the current language including fallback
- [x] when requesting the language which is the language of untranslated fields, return the original field. (`Blog.objects.filter(title_i18n='foo')` with `en` as active language.)
- [x] order by `title_i18n` to automagically order by the active language (with fallback).
- [x] filter by `title_i18n` to automagically filter by the active language (with fallback).


# After this is fully functional and there is 3rd party interest such features
 - [ ] Investigate using [MySQL JSON field](http://django-mysql.readthedocs.io/en/latest/model_fields/json_field.html)
