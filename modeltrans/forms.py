# -*- coding: utf-8 -*-
from django import forms


# from django.core import validators


# from modeltrans.fields import TranslationFieldProxy


class TranslationModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TranslationModelForm, self).__init__(*args, **kwargs)
        for f in self._meta.model._meta.fields:
            print(f)
