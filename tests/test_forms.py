# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms import ModelForm
from django.test import TestCase
from django.utils.translation import override

from .app.models import Blog


class ModelFormTest(TestCase):
    def test_modelform(self):
        class BlogForm(ModelForm):
            class Meta:
                model = Blog
                fields = ("title_i18n", "body_i18n")

        article = Blog(title="English", title_nl="Nederlands")

        with override("nl"):
            form = BlogForm(
                instance=article, data={"title_i18n": "Nederlandse taal", "body_i18n": "foo"}
            )
            form.save()

        article.refresh_from_db()
        self.assertEqual(article.title_nl, "Nederlandse taal")
        self.assertEqual(article.title_en, "English")

        with override("en"):
            form = BlogForm(
                instance=article, data={"title_i18n": "English language", "body_i18n": "foo"}
            )
            form.save()

        article.refresh_from_db()
        self.assertEqual(article.title_nl, "Nederlandse taal")
        self.assertEqual(article.title_en, "English language")
