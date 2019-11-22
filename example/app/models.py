from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.urls import reverse

from modeltrans.fields import TranslationField


class Category(models.Model):
    name = models.CharField(max_length=255)

    i18n = TranslationField(fields=("name",))

    class Meta:
        indexes = [GinIndex(fields=["i18n"])]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name_i18n


class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)

    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)

    i18n = TranslationField(fields=("title", "body"))

    class Meta:
        indexes = [GinIndex(fields=["i18n"])]

    def __str__(self):
        return self.title_i18n

    def get_absolute_url(self):
        return reverse("blog_detail", args=(self.pk,))
