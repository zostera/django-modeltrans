# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class RegistrationConfig(AppConfig):
    name = 'modeltrans'
    verbose = 'Django modeltrans using a registry.'

    def ready(self):
        from modeltrans.models import handle_translation_registrations
        handle_translation_registrations()
