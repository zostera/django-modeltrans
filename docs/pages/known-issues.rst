Known issues
============

We use django-modeltrans in production, but some aspects of it's API might be a bit surprising.
This page lists the issue we are aware of.
Some might get fixed at some point, some are just the result of database or Django implementations.

Reading the explanation of the :ref:`inner_workings` might also help to understand some of these issues.

Unsupported QuerySet methods
----------------------------
Using translated fields in ``QuerySet``/``Manager`` methods
``.distinct()``, ``.extra()``, ``.aggregate()``, ``.update()`` is not supported.


Fields supported
----------------
Behavior is tested using ``CharField()`` en ``TextField()``, as these make most sense for translated values.
Additional fields could make sense, and will likely work, but need extra test coverage.


Ordering defined in `Model.Meta.ordering`
-----------------------------------------
Any ordering using translated fields defined in ``Model.Meta.ordering`` is only supported with
Django 2.0 and later (`django/django#8473 <https://github.com/django/django/pull/8673>`_ is required).


Context of 'current language'
-----------------------------
Lookups (`<field>_i18n`) are translated when the line they are defined on is executed::

    class Foo():
        qs = Blog.objects.filter(title_i18n__contains='foo')

        def get_blogs(self):
            return self.qs

When ``Foo.get_blogs()`` will be called in the request cycle, one might expect the current language
for that request to define the ``title_i18n__contains`` filter.
But instead, the language active while creating the class ``Foo`` will be used.

For example the `queryset` argument to `ModelChoiceField()`.
See `github issue #34 <https://github.com/zostera/django-modeltrans/issues/34>`_
