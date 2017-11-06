Database performance
====================

Adding gin indexes
++++++++++++++++++

In order to perform well while performing filtering or ordering on translated values,
the ``i18n``-field need a GIN index. For django 1.11 and later, the index is added
automatically, for django 1.9 and 1.10, refer to :ref:`add_gin_index`.
