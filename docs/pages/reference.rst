API Reference
=============

Public API
----------

`modeltrans.admin`
~~~~~~~~~~~~~~~~~~
.. autoclass:: modeltrans.admin.ActiveLanguageMixin


`modeltrans.apps`
~~~~~~~~~~~~~~~~~
.. autoclass:: modeltrans.apps.RegistrationConfig


`modeltrans.fields`
~~~~~~~~~~~~~~~~~~~
.. autoclass:: modeltrans.fields.TranslatedVirtualField
  :members: get_field_name, get_language

.. autoclass:: modeltrans.fields.TranslationField


Internal API
------------

There should be no need to interact with these APIs, but it might be interesting when
working on django-modeltrans or to gain better understending of the internals.


`modeltrans.manager`
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: modeltrans.manager.MultilingualManager
.. autoclass:: modeltrans.manager.MultilingualQuerySet
