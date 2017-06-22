# -*- coding: utf-8 -*-

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import Manager

from . import settings
from .fields import translated_field_factory
from .manager import MultilingualManager, transform_translatable_fields


def check_languages(languages, model):
    valid_languages = list(settings.AVAILABLE_LANGUAGES) + list((settings.DEFAULT_LANGUAGE, ))
    for l in languages:
        if l not in valid_languages:
            raise ImproperlyConfigured(
                'Language "{}" is in required_languages on Model "{}" but '
                'not in settings.AVAILABLE_LANGUAGES.'.format(l, model.__name__)
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
                'Fields argument to TranslationField contains an item "{}", '
                'which is not a field (missing a comma?).'.format(field)
            )

    # TODO: apply more validation to the options
    if i18n_field.required_languages:
        if isinstance(i18n_field.required_languages, (tuple, list)):
            check_languages(i18n_field.required_languages, Model)
        else:
            check_languages(i18n_field.required_languages.keys(), Model)

        for fieldnames in i18n_field.required_languages.values():
            for field in fieldnames:
                if field not in i18n_field.fields:
                    raise ImproperlyConfigured(
                        'Fieldname "{}" in required_languages which is not '
                        'defined as translatable for Model "{}".'.format(field, Model.__name__)
                    )


def raise_if_field_exists(model, field_name):
    if not hasattr(model, field_name):
        return

    # Check if are not dealing with abstract field inherited.
    for cls in model.__mro__:
        if hasattr(cls, '_meta') and cls.__dict__.get(field_name, None):
            cls_opts = translator._get_options_for_model(cls)
            if not cls._meta.abstract or field_name not in cls_opts.local_fields:
                raise ValueError(
                    'Error adding translation field. Model "{}" already contains '
                    'a field named "{}".'.format(
                        model._meta.object_name, field_name
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
        # <original_field_name>_<DEFAULT_LANGUAGE>
        field = translated_field_factory(
            original_field=original_field,
            language=settings.DEFAULT_LANGUAGE,
            blank=True,
            null=True,
            editable=False,
        )
        raise_if_field_exists(Model, field.get_field_name())
        field.contribute_to_class(Model, field.get_field_name())

        # now, for each language, add a virtual field to get the tranlation for
        # that specific langauge
        # <original_field_name>_<language>
        for language in list(settings.AVAILABLE_LANGUAGES):
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
