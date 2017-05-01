# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError

from .utils import get_language


class TranslatedVirtualFieldValidator(object):
    def __init__(self, original_field, translation_options, language=None):
        self.original_field = original_field
        self.translation_options = translation_options
        self.language = language or get_language()

    def __call__(self, value):
        opts = self.translation_options
        original_field = self.original_field
        language = self.language

        if language in opts.required_languages:
            if value in (None, ''):
                raise ValidationError(
                    'Translation for field "{}" in "{}" is required'.format(original_field, language)
                )
