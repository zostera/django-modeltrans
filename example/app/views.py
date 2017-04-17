# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import django_tables2 as tables
from django.db import models
from django.db.models import CharField, TextField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Cast, Coalesce
from django.shortcuts import render

from sqlparse import format as format_sql

from .models import Blog, BlogI18n


class Table(tables.Table):
    data = tables.TemplateColumn(template_name='datatable.html')
    query = tables.TemplateColumn(template_name='query.html')


class DataTable(tables.Table):
    class Meta:
        model = Blog


def index(request):
    test_qs = [
        # # has_key, PostgreSQL operator  '?'
        Blog.objects.filter(i18n__has_key='title_fr'),
        #
        # # order by RawSQL
        # Blog.objects.order_by(RawSQL('i18n->>%s', ('title_nl', ))),
        #
        # # order by RawSQL is not possible like this:
        # # Blog.objects.order_by(RawSQL('i18n->>%s DESC', ('title_nl', ))),
        # # (will result in ORDER BY i18n->>nl DESC DESC) must use an annotated field
        #
        # # order by annotated field
        # Blog.objects.annotate(
        #     title_i18n=RawSQL('i18n->>%s', ('title_nl',))
        # ).order_by('-title_i18n'),

        # order by annotated field coalesce'd with original field.
        # Blog.objects.annotate(
        #     title_i18n=Coalesce('title', RawSQL('i18n->>%s', ('title_nl',)))
        # ).order_by('-title_i18n'),

        # when reversing the arguments to Coalesce, it suddenly complains about
        # the type, an output_field argument needs to be set:
        Blog.objects.annotate(
            title_i18n=Coalesce(RawSQL('i18n->>%s', ('title_nl',)), 'title', output_field=CharField())
        ).order_by('-title_i18n'),

        # full text search op
        # https://github.com/django/django/pull/6965
        Blog.objects.annotate(
            title_i18n=models.Func('i18n', template="%(expressions)s ->> 'title_nl'", output_field=models.TextField())
        ).filter(title_i18n__contains='al'),

        Blog.objects.annotate(
            title_nl=Coalesce(RawSQL('i18n->>%s', ('title_nl',)), 'title', output_field=CharField())
        ).filter(title_nl__contains='al'),

    ]

    tables = []
    for q in test_qs:
        tables.append({
            'data': DataTable(q),
            'query': format_sql(str(q.query), reindent=True)
        })

    return render(request, 'index.html', {
        'table': Table(tables)
    })

def test(request):
    return render(request, 'index.html', {
        'table': DataTable(BlogI18n.objects.all().order_by('title_nl'))
    })

def fixtures(request):
    Blog.objects.all().delete()
    with open('data/species.json') as f:
        data = json.load(f)

        for item in data:
            Blog.objects.create(title=item['title'], i18n=item.get('i18n', None))

    return render(request, 'index.html', {
        'table': DataTable(Blog.objects.all())
    })
