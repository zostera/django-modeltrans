# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Site(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(null=True)

    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    occupation = models.CharField(max_length=255)
