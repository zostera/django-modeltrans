# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from modeltrans.fields import TranslationField
from modeltrans.manager import MultilingualManager


class CategoryQueryset(models.QuerySet):
    """
    Custom manager to make sure pickling on-the-fly created classes
    can be pickled, see test_querysets.py::PickleTest
    """


class Category(models.Model):
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    i18n = TranslationField(fields=("name", "title"))

    objects = CategoryQueryset.as_manager()

    def __str__(self):
        return self.name


class Site(models.Model):
    name = models.CharField(max_length=255)

    objects = MultilingualManager()

    def __str__(self):
        return self.name


class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(null=True)

    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.CASCADE)

    i18n = TranslationField(fields=("title", "body"), required_languages=("nl",))

    def __str__(self):
        return self.title


class SeoBlog(Blog):

    seo_title = models.CharField(max_length=255)
    i18n_fields = ["title", "body", "seo_title"]


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    occupation = models.CharField(max_length=255)

    i18n = TranslationField(fields=("occupation",), required_languages=("en", "nl"))


class TextModel(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()

    i18n = TranslationField(fields=("title", "description"))

    def __str__(self):
        return self.title


class NullableTextModel(models.Model):
    description = models.TextField(null=True)

    i18n = TranslationField(fields=("description",))

    def __str__(self):
        return self.title


# copy of attributes in ringbase
class Attribute(models.Model):
    slug = models.SlugField(verbose_name=_("slug"), unique=True)
    name = models.CharField(_("name"), max_length=100, db_index=True)

    i18n = TranslationField(fields=("name",))

    def __str__(self):
        return self.name_i18n


class Choice(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(_("value"), max_length=100, blank=True, db_index=True)
    name = models.CharField(_("name"), max_length=100, blank=True, db_index=True)
    description = models.TextField(_("description"), blank=True)
    sort_order = models.IntegerField(_("sort order"), default=0, db_index=True)

    i18n = TranslationField(fields=("name", "description"))


class AbstractBaseAttr(models.Model):
    """
    An abstract Base Class used to generate actual Attr classes
    """

    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = JSONField(null=True, blank=True)

    class Meta:
        abstract = True


def createBaseAttr(model):
    class GeneratedAttr(AbstractBaseAttr):
        """
        An abstract Base Class used to generate actual Attr classes
        with an object
        """

        object = models.ForeignKey(model, related_name="attrs", on_delete=models.CASCADE)

        _model = model

        class Meta:
            abstract = True
            unique_together = (("attribute", "object"),)

    return GeneratedAttr


class BlogAttr(createBaseAttr(Blog)):
    pass
