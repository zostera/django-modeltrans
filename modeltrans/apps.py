# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.apps
from django.apps import AppConfig

from .translator import translate_model


class RegistrationConfig(AppConfig):
    name = 'modeltrans'
    verbose_name = 'Django modeltrans using a registry.'

    def ready(self):
        for Model in django.apps.apps.get_models():
            translate_model(Model)
