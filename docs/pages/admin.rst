.. _admin:

Admin
=====

By default, each field is displayed for each language configured for django-modeltrans.
This might work for a couple of languages, but with 2 translated fields and 10 languages,
it already is a bit unwieldy.

The `ActiveLanguageMixin` is provided to show only the default language (`settings.LANGUAGE_CODE`) and
the currently active language. Use like this::

    from django.contrib import admin
    from modeltrans.admin import ActiveLanguageMixin

    from .models import Blog


    @admin.register(Blog)
    class BlogAdmin(ActiveLanguageMixin, admin.ModelAdmin):
        pass
