from __future__ import unicode_literals

import sqlparse
from django import template

register = template.Library()


@register.filter
def sqlformat(sql):
    return sqlparse.format(str(sql), reindent=True)
