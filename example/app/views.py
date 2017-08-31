# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import django_tables2 as tables
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django_filters import FilterSet
from django_filters.views import FilterView

from .models import Blog


class BlogTable(tables.Table):
    edit = tables.TemplateColumn(
        template_code='''<a href="{% url 'blog-edit' pk=record.pk %}" class="btn btn-small">edit</a>''',
        empty_values=(),
        orderable=False
    )

    class Meta:
        model = Blog
        fields = (
            # this field should fallback to LANGUAGE_CODE
            'title_i18n',
            'title_en',
            'title_nl',
            'title_de',
            'title_fr',
            'category',
            'i18n'
        )


class BlogFilter(FilterSet):
    class Meta:
        model = Blog
        fields = {
            'title_i18n': ['exact', 'contains'],
            'category': ['exact']
        }


class BlogListView(tables.SingleTableView):
    table_class = BlogTable
    model = Blog
    template_name = 'table.html'


class FilteredBlogListView(FilterView, tables.SingleTableView):
    table_class = BlogTable
    model = Blog
    template_name = 'table.html'

    filterset_class = BlogFilter


class BlogView(DetailView):
    model = Blog
    template_name = 'blog.html'


class BlogUpdateView(UpdateView):
    model = Blog
    fields = ['title', 'title_nl', 'body', 'category']
    template_name = 'blog_update_form.html'
    template_name_suffix = '_update_form'

    success_url = reverse_lazy('blogs')


def fixtures(request):
    Blog.objects.all().delete()
    with open('data/species.json') as f:
        data = json.load(f)

        for item in data:
            Blog.objects.create(title=item['title'], i18n=item.get('i18n', None))

    return redirect('blogs')
