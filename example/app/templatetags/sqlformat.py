from __future__ import unicode_literals

import sqlparse
from django import template

register = template.Library()


@register.filter
def sqlformat(sql):
    """
    Format SQL queries.
    """
    return sqlparse.format(str(sql), reindent=True, wrap_after=120)
