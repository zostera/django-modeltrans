# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.db import models


class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(null=True)

    i18n = JSONField(editable=False, null=True)
    translatable = ('title', )

    def __str__(self):
        return self.title

    def __getattr__(self, key):
        key_original = key[0:key.rfind('_')]

        if '_' not in key_original and key_original not in self.translatable:
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(self.__class__.__name__, key)
            )
        lang = key[key.rfind('_') + 1:]

        if self.i18n and key in self.i18n:
            return self.i18n[key]
        else:
            raise AttributeError(
                "'{}.title' has no translation '{}'".format(self.__class__.__name__, lang)
            )
