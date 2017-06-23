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
                i18n_field = Model._meta.get_field('i18n')
            except FieldDoesNotExist:
                continue

            if not isinstance(i18n_field, TranslationField):
                # TODO: warning?
                continue

            if not i18n_field.virtual_fields:
                # This mode is required for the migration process:
                # It needs to have a stage where we do have the TranslationField,
                # but not the virtual fields, to be able to copy the original values.
                continue

            add_manager(Model)
            add_virtual_fields(Model, i18n_field.fields, i18n_field.required_languages)
            patch_constructor(Model)
