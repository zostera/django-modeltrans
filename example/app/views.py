# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import django_tables2 as tables
from django.db.models.expressions import RawSQL
from django.shortcuts import render
from django.utils.html import format_html

from .models import Blog


class Table(tables.Table):
    data = tables.TemplateColumn(template_name='datatable.html')
    query = tables.TemplateColumn(template_name='query.html')

    class Meta:
        template = 'django_tables2/bootstrap.html'
        attrs = {
            'class': 'table table-compact table-striped'
        }


class DataTable(tables.Table):
    class Meta:
        model = Blog
        template = 'django_tables2/bootstrap.html'
        attrs = {
            'class': 'table table-compact table-striped'
        }

    def render_i18n(self, value):
        if value is None:
            return '-'
        return format_html('<pre>{}</pre>', json.dumps(value, indent=2))


def index(request):
    test_qs = [
        # has_key, PostgreSQL operator  '?'
        Blog.objects.filter(i18n__has_key='title_nl'),

        # order by RawSQL
        Blog.objects.order_by(RawSQL('i18n->>%s', ('title_nl', ))),
        # order by RawSQL is not possible like this, must use an annotaed field
        # Blog.objects.order_by(RawSQL('i18n->>%s DESC', ('title_nl', ))),

        # order by annotated field
        Blog.objects.annotate(title_i18n=RawSQL('i18n->>%s', ('title_nl',))).order_by('-title_i18n'),
    ]

    tables = []
    for q in test_qs:
        tables.append({
            'data': DataTable(q),
            'query': str(q.query).replace('FROM', '\nFROM').replace('WHERE', '\nWHERE').replace('ORDER BY', '\nORDER BY')
        })

    return render(request, 'index.html', {
        'table': Table(tables)
    })
