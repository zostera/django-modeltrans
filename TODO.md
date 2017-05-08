 # django-modeltrans TODO

 - [*] Verify that null by default is ok.
 - [*] POC working in an example project
  - [*] Filtering/excluding
  - [*] Ordering
  - [*] Fallback to base language while ordering
  - [*] `Model.objects.get()``

 - [ ] Building a package django-modeltrans on the POC
  - [*] read translatable fields from `TranslationOptions`, not from the model
        attribute.
  - [ ] filtering spanning relations
        `Category.objects.filter(blog__title_nl__contains='al')`

  - [*] create(title='...', title_nl='...'),
  - [*] and Model(title_nl='')
        Allow calling `create(title_nl='...')` and `Model(title_nl='...').save()`
        with translated versions of a field and make sure they arrive in the
        `i18n` field.
  - [*] assigning to translated fields: `m = Model(...), m.title_nl = 'foo', m.save()`
  - [ ] rewrite fieldnames in `F` expressions (https://github.com/deschler/django-modeltranslation/blob/master/modeltranslation/manager.py#L314)
  - [ ] deferred fields `defer()`, `only()`
  - [*] clean() and requiredness of translated fields.
  - [ ] values()
  - [ ] values_list()
  - [ ] select_related()
  - [*] Getting translated fields on a Model instance (if not annotated) (inject a __getattr__ on a Model?)
  - [*] Registration of translatable models and fields
    - [*] Remove the need of manually adding the `Manager` to the objects attribute
    - [*] inject the `i18n` field in the models.
    - [*] inject `__getattr__` to allow access to the translated fields
  - [ ] Tests
    - [*] Test suite runnable using `tox`.
    - [ ] Test suite runnable in travisci
  - [*] ModelForm integration
  - [*] Django admin integration
  - [ ] Migration from django-model-translation
      - [ ] copy values from existing fields into the `i18n` field
      - [ ] remove the `<original_field>_<lang>` fields
      - [ ] move the value of `i18n.<original_field>_<DEFAULT_LANG>` to `<original_field>`
  - [ ] Documentation

# usage of managers/models in code

- [*] have a `title_i18n` field to get the translated version for the current language including fallback
- [*] when requesting the language which is the language of untranslated fields, return the original field. (`Blog.objects.filter(title_i18n='foo')` with `en` as active language.)
- [*] order by `title_i18n` to automagically order by the active language (with fallback).
- [*] filter by `title_i18n` to automagically filter by the active language (with fallback).


# After this is fully functional and there is 3rd party interest such features
 - [ ] Investigate using [MySQL JSON field](http://django-mysql.readthedocs.io/en/latest/model_fields/json_field.html)
