# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.apps
from django.apps import AppConfig
from django.core.exceptions import FieldDoesNotExist


class RegistrationConfig(AppConfig):
    name = 'modeltrans'
    verbose_name = 'Django modeltrans using a registry.'

    def ready(self):
        from .fields import TranslationField
        from .translator import add_virtual_fields, add_manager, patch_constructor

        for Model in django.apps.apps.get_models():
            try:
                field = Model._meta.get_field('i18n')
            except FieldDoesNotExist:
                continue

            if not isinstance(field, TranslationField):
                # TODO: warning?
                continue

            add_manager(Model)
            add_virtual_fields(Model, field.fields, field.required_languages)
            patch_constructor(Model)
