# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django_tables2 as tables
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from .models import Blog


class BlogTable(tables.Table):

    edit = tables.TemplateColumn(
        template_code='''<a href="{% url 'blog' pk=record.pk %}" class="btn btn-small">edit</a>''',
        empty_values=()
    )

    class Meta:
        model = Blog
        fields = ('title_i18n', 'title_nl', 'category')


class BlogListView(tables.SingleTableView):
    table_class = BlogTable
    model = Blog
    template_name = 'table.html'


class BlogView(DetailView):
    model = Blog
    template_name = 'blog.html'


class BlogUpdateView(UpdateView):
    model = Blog
    fields = ['title', 'body']
    template_name = 'blog_update_form.html'
    template_name_suffix = '_update_form'
