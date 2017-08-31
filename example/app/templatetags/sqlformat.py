from __future__ import unicode_literals

from django import template
import sqlparse

register = template.Library()


@register.filter
def sqlformat(sql):
    '''
    Format SQL queries.
    '''
    return sqlparse.format(str(sql), reindent=True, wrap_after=120)
