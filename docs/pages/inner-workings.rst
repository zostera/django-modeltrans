Inner workings
==============

Django-modeltrans uses a `django.contrib.postgres.JSONField` to store field
translations in the table and adds some augmentation to the queries made by
Django's QuerySet methods to allow transparent use of the translated values.

The inner workings are illustrated using this model::

    class Blog(models.Model):
        title = models.CharField(max_length=255)
        body = models.TextField(null=True)

        i18n = TranslationField(fields=('title', 'body'))

When creating an object, translated fields in the constructor are transformed
into a value in the i18n field. So the following two calls are equivalent::

    Blog.objects.create(title='Falcon', title_nl='Valk', title_de='Falk')
    Blog.objects.create(title='Falcon', i18n={'title_nl': 'Valk', 'title_de': 'Falk'})

So adding a translated field does not need any migrations: it just requires
adding a key to the ``i18n`` field.

When selecting objects django-modeltrans replaces any occurrence of a translated
field with the appropriate jsonb key get operation::

    Blog.objects.filter(title_nl='Valk')
    # SELECT ... FROM "app_blog" WHERE (app_blog.i18n->>'title_nl')::varchar(255) = 'Valk'

    Blog.objects.filter(title_nl__contains='a')
    # SELECT ... FROM "app_blog" WHERE (app_blog.i18n->>'title_nl')::varchar(255) LIKE '%a%'

In addition to that, you can use ``<fieldname>_i18n`` to filter on. That will use
`COALESCE` to look in both the currently active language and the default
language::

    from django.utils.translation import override

    with override('nl'):
        Blog.objects.filter(title_i18n='Valk')

    # SELECT ... FROM "app_blog"
    # WHERE COALESCE((app_blog.i18n->>'title_nl'), "app_blog"."title") = 'Valk'

Model objects containing translated fields get virtual fields for each field/
language combination plus a field which always returns the active language.
In the example, we have configured 3 translation languages: ``('nl', 'de', 'fr')``
resulting in 4 virtual fields for each original field::

    b = Blog.objects.create(title='Falcon', title_nl='Valk', title_de='Falk')
    b._meta.get_fields()

    (<django.db.models.fields.AutoField: id>,
     <django.db.models.fields.CharField: title>,
     <django.db.models.fields.TextField: body>,
     <django.db.models.fields.related.ForeignKey: category>,
     <modeltrans.fields.TranslationField: i18n>,
     <modeltrans.fields.TranslatedCharField: title_i18n>,
     <modeltrans.fields.TranslatedCharField: title_en>,
     <modeltrans.fields.TranslatedCharField: title_nl>,
     <modeltrans.fields.TranslatedCharField: title_de>,
     <modeltrans.fields.TranslatedCharField: title_fr>,
     <modeltrans.fields.TranslatedTextField: body_i18n>,
     <modeltrans.fields.TranslatedTextField: body_en>,
     <modeltrans.fields.TranslatedTextField: body_nl>,
     <modeltrans.fields.TranslatedTextField: body_de>,
     <modeltrans.fields.TranslatedTextField: body_fr>)

Each virtual field for an explicit language will only return a value if that
language is defined::

    print(b.title_nl, b.title_fr)
    # 'Valk', None

The virtual field ``<field>_i18n`` returns the translated value for the current
active language and falls back to the language in ``LANGUAGE_CODE``::

    with override('nl'):
        print(b.title_i18n)
    # 'Valk'

    with override('de'):
        print(b.title_i18n)
    # 'Falk'

    with override('fr'):
        print(b.title_i18n)
    # 'Falcon' (no french translation available, falls back to LANGUAGE_CODE)

Django-modeltrans also allows ordering on translated values. Ordering on
``<field>_i18n`` probably makes most sense, as it more likely that there is a
value to order by::

    with override('de'):
        qs = Blog.objects.order_by('title_i18n')

    # SELECT ...,
    # FROM "app_blog"
    # ORDER BY COALESCE((app_blog.i18n->>'title_de'), "app_blog"."title") ASC

Results in the following ordering::

    title_i18n   title_en     title_nl     title_de
    ------------ ------------ ------------ ------------
    Crayfish     Crayfish
    Delfine      Dolphin      Dolfijn      Delfine
    Dragonfly    Dragonfly    Libellen
    Duck         Duck         Eend
    Falk         Falcon       Valk         Falk
    Frog         Frog         Kikker
    Kabeljau     Cod                       Kabeljau
    Toad         Toad         Pad

As you can see, although the german translations are not complete, ordering on
``title_i18n`` still results in a useful ordering.

.. note::

    These examples assume the default setting for `MODELTRANS_FALLBACK`.
    If you customize that setting, it can get slightly more complex, resulting
    in more than 2 arguments to the `COALESCE` function.
