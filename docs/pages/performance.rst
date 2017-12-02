Database performance
====================

Adding gin indexes
++++++++++++++++++

In order to perform well while performing filtering or ordering on translated values,
the ``i18n``-field need a GIN index. The index is added automatically, for every
supported Django version.
