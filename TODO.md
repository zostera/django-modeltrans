 # django-modeltranslation2 TODO

 - [*] Verify that null by default is ok.
 - [*] POC working in an example project
  - [*] Filtering/excluding
  - [*] Ordering
  - [*] Fallback to base language while ordering
  - [*] `Model.objects.get()``

 - [ ] Building a package django-modeltranslation2 on the POC
  - [*] read translatable fields from `TranslationOptions`, not from the model
        attribute.
  - [ ] filtering spanning relations
        Category.objects.filter(blog__title_nl__contains='al')

  - [*] create(title='...', title_nl='...'),
  - [*] and Model(title_nl='')
        Allow calling `create(title_nl='...')` and `Model(title_nl='...').save()`
        with translated versions of a field and make sure they arrive in the
        `i18n` field.
  - [ ] deferred fields `defer()`, `only()`
  - [ ] clean() and requiredness of translated fields.
  - [ ] values()
  - [ ] values_list()
  - [ ] select_related()
  - [ ] spanning relations
  - [*] Getting translated fields on a Model instance (if not annotated) (inject a __getattr__ on a Model?)
  - [*] Registration of translatable models and fields
    - [*] Remove the need of manually adding the `Manager` to the objects attribute
    - [*] inject the `i18n` field in the models.
    - [*] inject `__getattr__` to allow access to the translated fields
  - [ ] Tests
    - [*] Test suite runnable using `tox`.
    - [ ] Test suite runnable in travisci
  - [ ] ModelForm integration
  - [ ] Django admin integration
  - [ ] Migration from django-model-translation


# After this is fully functional and there is 3rd party interest such features
 - [ ] Investigate using [MySQL JSON field](http://django-mysql.readthedocs.io/en/latest/model_fields/json_field.html)
