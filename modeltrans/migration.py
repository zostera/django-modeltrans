# -*- coding: utf-8 -*-
from __future__ import unicode_literals


# try:
#     from modeltranslation.translator import translator
#     DJANGO_MODELTRANSLATION_AVAILABLE = True
# except ImportError:
#     DJANGO_MODELTRANSLATION_AVAILABLE = False


def copy_translations(model, fields):
    for m in model.objects.all():
        for field in fields:
            m.i18n[field] = getattr(m, field)

        m.save()
