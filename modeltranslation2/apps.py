# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class RegistrationConfig(AppConfig):
    name = 'modeltranslation2'
    verbose = 'Django modeltranslation2 using a registry.'

    def ready(self):
        from modeltranslation2.models import handle_translation_registrations
        handle_translation_registrations()
