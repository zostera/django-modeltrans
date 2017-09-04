# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.apps
from django.apps import AppConfig

from .conf import check_fallback_chain
from .translator import translate_model


class RegistrationConfig(AppConfig):
    name = 'modeltrans'
    verbose_name = 'Django modeltrans using a registry.'

    def ready(self):
        check_fallback_chain()

        for Model in django.apps.apps.get_models():
            translate_model(Model)
