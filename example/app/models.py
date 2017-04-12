# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.db import models

from .manager import MultilingualQuerySetManager


class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(null=True)

    i18n = JSONField(editable=False, null=True)

    # objects = MultilingualQuerySetManager()

    translatable = ('title', 'body')

    def __str__(self):
        return self.title

class BlogI18n(Blog):
    # proxy model to test MultilingualQuerySetManager without
    # compromising the original's functionality

    objects = MultilingualQuerySetManager()
    class Meta(object):
        proxy = True
