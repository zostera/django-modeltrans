# -*- coding: utf-8 -*-

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import Manager

from .conf import get_available_languages, get_default_language
from .fields import TranslationField, translated_field_factory
from .manager import MultilingualManager, transform_translatable_fields


def translate_model(Model):
    try:
        i18n_field = Model._meta.get_field('i18n')
    except FieldDoesNotExist:
        return

    if not isinstance(i18n_field, TranslationField):
        return

    if not i18n_field.virtual_fields:
        # This mode is required for the migration process:
        # It needs to have a stage where we do have the TranslationField,
        # but not the virtual fields (which would collide with the
        # django-modeltranslation `<field>_<lang>`-fields), to be able to
        # copy the values from the `<field>_<lang>`-fields into `i18n.<field>_<lang>`.
        return

    validate(Model)

    add_manager(Model)
    add_virtual_fields(Model, i18n_field.fields, i18n_field.required_languages)
    patch_constructor(Model)


def check_languages(languages, model):
    for l in languages:
        if l not in get_available_languages():
            raise ImproperlyConfigured(
                'Language "{}" is in required_languages on Model "{}" but '
                'not in settings.MODELTRANS_AVAILABLE_LANGUAGES.'.format(l, model.__name__)
            )


def validate(Model):
    '''
    Perform validation of the arguments to TranslationField
    '''
    i18n_field = Model._meta.get_field('i18n')
    for field in i18n_field.fields:
        try:
            Model._meta.get_field(field)
        except FieldDoesNotExist:
            raise ImproperlyConfigured(
                'Argument "fields" to TranslationField contains an item "{}", '
                'which is not a field (missing a comma?).'.format(field)
            )

    if i18n_field.required_languages:
        if isinstance(i18n_field.required_languages, (tuple, list)):
            check_languages(i18n_field.required_languages, Model)
        else:
            check_languages(i18n_field.required_languages.keys(), Model)

        for fieldnames in i18n_field.required_languages:
            if field not in i18n_field.fields:
                raise ImproperlyConfigured(
                    'Fieldname "{}" in required_languages which is not '
                    'defined as translatable for Model "{}".'.format(field, Model.__name__)
                )


def raise_if_field_exists(Model, field_name):
    if not hasattr(Model, field_name):
        return

    try:
        Model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return

    raise ImproperlyConfigured(
        'Error adding translation field. Model "{}" already contains '
        'a field named "{}".'.format(
            Model._meta.object_name, field_name
        )
    )


def add_virtual_fields(Model, fields, required_languages):
    '''
    Adds newly created translation fields to the given translation options.
    '''
    # proxy fields to assign and get values from.
    for field_name in fields:
        original_field = Model._meta.get_field(field_name)

        # first, add a `<original_field_name>_i18n` virtual field to get the currently
        # active translation for a field
        field = translated_field_factory(
            original_field=original_field,
            blank=True,
            null=True,
            editable=False  # disable in admin
        )

        raise_if_field_exists(Model, field.get_field_name())
        field.contribute_to_class(Model, field.get_field_name())

        # add a virtual field pointing to the original field with name
        # <original_field_name>_<LANGUAGE_CODE>
        field = translated_field_factory(
            original_field=original_field,
            language=get_default_language(),
            blank=True,
            null=True,
            editable=False,
        )
        raise_if_field_exists(Model, field.get_field_name())
        field.contribute_to_class(Model, field.get_field_name())

        # now, for each language, add a virtual field to get the tranlation for
        # that specific langauge
        # <original_field_name>_<language>
        for language in get_available_languages(include_default=False):
            blank_allowed = language not in required_languages
            field = translated_field_factory(
                original_field=original_field,
                language=language,
                blank=blank_allowed,
                null=blank_allowed
            )
            raise_if_field_exists(Model, field.get_field_name())
            field.contribute_to_class(Model, field.get_field_name())


def has_custom_queryset(manager):
    '''
    Check whether manager (or its parents) has declared some custom get_queryset method.
    '''
    return getattr(manager, 'get_queryset', None) != getattr(Manager, 'get_queryset', None)


def add_manager(model):
    '''
    Monkey patches the original model to use MultilingualManager instead of
    default managers (not only ``objects``, but also every manager defined and inherited).

    Custom managers are merged with MultilingualManager.
    '''
    if model._meta.abstract:
        return

    def patch_manager_class(manager):
        if isinstance(manager, MultilingualManager):
            return
        if manager.__class__ is Manager:
            manager.__class__ = MultilingualManager
        else:
            class NewMultilingualManager(MultilingualManager, manager.__class__):
                use_for_related_fields = getattr(
                    manager.__class__, 'use_for_related_fields', not has_custom_queryset(manager))
                _old_module = manager.__module__
                _old_class = manager.__class__.__name__

                def deconstruct(self):
                    return (
                        False,  # as_manager
                        '%s.%s' % (self._old_module, self._old_class),  # manager_class
                        None,  # qs_class
                        self._constructor_args[0],  # args
                        self._constructor_args[1],  # kwargs
                    )

            manager.__class__ = NewMultilingualManager

    managers = model._meta.local_managers
    for current_manager in managers:
        prev_class = current_manager.__class__
        patch_manager_class(current_manager)
        if model._default_manager.__class__ is prev_class:
            # Normally model._default_manager is a reference to one of model's managers
            # (and would be patched by the way).
            # However, in some rare situations (mostly proxy models)
            # model._default_manager is not the same instance as one of managers, but it
            # share the same class.
            model._default_manager.__class__ = current_manager.__class__
    patch_manager_class(model._base_manager)
    if hasattr(model._meta, '_expire_cache'):
        model._meta._expire_cache()


def patch_constructor(model):
    '''
    Monkey patches the original model to rewrite fields names in __init__
    '''
    old_init = model.__init__

    def patched_init(self, *args, **kwargs):
        old_init(self, *args, **transform_translatable_fields(self.__class__, kwargs))
    model.__init__ = patched_init
