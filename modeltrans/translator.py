# -*- coding: utf-8 -*-

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import Manager
from django.db.models.base import ModelBase
from django.utils.six import with_metaclass

from . import settings
from .exceptions import AlreadyRegistered, DescendantRegistered, NotRegistered
from .fields import TranslatedVirtualField, TranslationJSONField
from .manager import MultilingualManager, transform_translatable_fields


class FieldsAggregationMetaClass(type):
    '''
    Metaclass to handle custom inheritance of fields between classes.
    '''
    def __new__(cls, name, bases, attrs):
        attrs['fields'] = set(attrs.get('fields', ()))
        for base in bases:
            if isinstance(base, FieldsAggregationMetaClass):
                attrs['fields'].update(base.fields)
        attrs['fields'] = tuple(attrs['fields'])
        return super(FieldsAggregationMetaClass, cls).__new__(cls, name, bases, attrs)


class TranslationOptions(with_metaclass(FieldsAggregationMetaClass, object)):
    '''
    Translatable fields are declared by registering a model using
    ``TranslationOptions`` class with appropriate ``fields`` attribute.
    Model-specific fallback values and languages can also be given as class
    attributes.

    Options instances hold info about translatable fields for a model and its
    superclasses. The ``local_fields`` and ``fields`` attributes are mappings
    from fields to sets of their translation fields; ``local_fields`` contains
    only those fields that are handled in the model's database table (those
    inherited from abstract superclasses, unless there is a concrete superclass
    in between in the inheritance chain), while ``fields`` also includes fields
    inherited from concrete supermodels (giving all translated fields available
    on a model).

    ``related`` attribute inform whether this model is related part of some relation
    with translated model. This model may be not translated itself.
    ``related_fields`` contains names of reverse lookup fields.
    '''
    required_languages = ()

    def __init__(self, model):
        '''
        Create fields dicts without any translation fields.
        '''
        self.model = model
        self.registered = False
        self.related = False
        self.local_fields = dict((f, set()) for f in self.fields)
        self.fields = dict((f, set()) for f in self.fields)
        self.related_fields = []

    def validate(self, model):
        '''
        Perform validation of `TranslationOptions`.
        '''
        for field in self.fields.keys():
            try:
                self.model._meta.get_field(field)
            except FieldDoesNotExist:
                raise ImproperlyConfigured(
                    'Attribute {}.fields contains an item "{}", which is not a field (missing a comma?).'.format(
                        self.__class__.__name__,
                        field
                    )
                )

        # TODO: apply more validation to the options
        if self.required_languages:
            if isinstance(self.required_languages, (tuple, list)):
                self._check_languages(self.required_languages, model)
            else:
                self._check_languages(self.required_languages.keys(), model)

                for fieldnames in self.required_languages.values():
                    for field in fieldnames:
                        if field not in self.fields:
                            raise ImproperlyConfigured(
                                'Fieldname "{}" in required_languages which is not '
                                'defined as translatable for Model "{}".'.format(field, model.__name__)
                            )

    def _check_languages(self, languages, model):
        valid_languages = list(settings.AVAILABLE_LANGUAGES) + list((settings.DEFAULT_LANGUAGE, ))
        for l in languages:
            if l not in valid_languages:
                raise ImproperlyConfigured(
                    'Language "{}" is in required_languages on Model "{}" but '
                    'not in settings.AVAILABLE_LANGUAGES.'.format(l, model.__name__)
                )

    def update(self, other):
        '''
        Update with options from a superclass.
        '''
        if other.model._meta.abstract:
            self.local_fields.update(other.local_fields)
        self.fields.update(other.fields)

    def add_translation_field(self, field, translation_field):
        '''
        Add a new translation field to both fields dicts.
        '''
        self.local_fields[field].add(translation_field)
        self.fields[field].add(translation_field)

    def get_field_names(self):
        '''
        Return name of all fields that can be used in filtering.
        '''
        return list(self.fields.keys()) + self.related_fields

    def __str__(self):
        local = tuple(self.local_fields.keys())
        inherited = tuple(set(self.fields.keys()) - set(local))
        return '%s: %s + %s' % (self.__class__.__name__, local, inherited)


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


def add_translation_field(model, opts):
    '''
    Monkey patches the original model class to provide the `i18n` field.

    Adds newly created translation fields to the given translation options.
    '''
    # field to store the translations in
    model.add_to_class('i18n', TranslationJSONField())

    # proxy fields to assign and get values from.
    for field_name in opts.local_fields.keys():
        # first, add a `<original_field>_i18n` virtual field to get the currently
        # active translation for a field
        field = TranslatedVirtualField(
            original_field=field_name,
            blank=True,
            null=True,
            editable=False  # disable in admin
        )

        raise_if_field_exists(model, field.get_field_name())
        field.contribute_to_class(model, field.get_field_name())

        # add a virtual field pointing to the original field with name
        # <orignal_field>_<DEFAULT_LANGUAGE>
        field = TranslatedVirtualField(
            original_field=field_name,
            blank=True,
            null=True,
            editable=False,
            language=settings.DEFAULT_LANGUAGE
        )
        raise_if_field_exists(model, field.get_field_name())
        field.contribute_to_class(model, field.get_field_name())

        # now, for each language, add a virtual field to get the tranlation for
        # that specific langauge
        # <original_field>_<language>
        for language in list(settings.AVAILABLE_LANGUAGES):
            blank_allowed = language not in opts.required_languages
            field = TranslatedVirtualField(
                original_field=field_name,
                language=language,
                blank=blank_allowed,
                null=blank_allowed
            )
            raise_if_field_exists(model, field.get_field_name())
            field.contribute_to_class(model, field.get_field_name())


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
                    manager.__class__, "use_for_related_fields", not has_custom_queryset(manager))
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
    if hasattr(model._meta, "_expire_cache"):
        model._meta._expire_cache()


def patch_constructor(model):
    '''
    Monkey patches the original model to rewrite fields names in __init__
    '''
    old_init = model.__init__

    def patched_init(self, *args, **kwargs):
        old_init(self, *args, **transform_translatable_fields(self.__class__, kwargs))
    model.__init__ = patched_init


class Translator(object):
    '''
    A Translator object encapsulates an instance of a translator. Models are
    registered with the Translator using the register() method.
    '''
    def __init__(self):
        # All seen models (model class -> ``TranslationOptions`` instance).
        self._registry = {}

    def register(self, model_or_iterable, opts_class=None, **options):
        '''
        Registers the given model(s) with the given translation options.

        The model(s) should be Model classes, not instances.

        Fields declared for translation on a base class are inherited by
        subclasses. If the model or one of its subclasses is already
        registered for translation, this will raise an exception.
        '''
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]

        for model in model_or_iterable:
            # Ensure that a base is not registered after a subclass (_registry
            # is closed with respect to taking bases, so we can just check if
            # we've seen the model).
            if model in self._registry:
                if self._registry[model].registered:
                    raise AlreadyRegistered(
                        'Model "{}" is already registered for translation'.format(
                            model.__name__
                        )
                    )
                else:
                    descendants = [d.__name__ for d in self._registry.keys()
                                   if issubclass(d, model) and d != model]
                    print(descendants)
                    raise DescendantRegistered(
                        'Model "%s" cannot be registered after its subclass'
                        ' "%s"' % (model.__name__, descendants[0]))

            # Find inherited fields and create options instance for the model.
            opts = self._get_options_for_model(model, opts_class, **options)

            # If an exception is raised during registration, mark model as not-registered
            try:
                self._register_single_model(model, opts)
            except Exception:
                self._registry[model].registered = False
                raise

    def _register_single_model(self, model, opts):
        # Now, when all fields are initialized and inherited, validate configuration.
        opts.validate(model=model)

        # Mark the object explicitly as registered -- registry caches
        # options of all models, registered or not.
        opts.registered = True

        # Add translation fields to the model.
        if not model._meta.proxy:
            add_translation_field(model, opts)

        # Set MultilingualManager
        add_manager(model)

        # Patch __init__ to rewrite fields
        patch_constructor(model)

    def unregister(self, model_or_iterable):
        '''
        Unregisters the given model(s).

        If a model isn't registered, this will raise NotRegistered. If one of
        its subclasses is registered, `DescendantRegistered` will be raised.
        '''
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            # Check if the model is actually registered (``get_options_for_model``
            # throws an exception if it's not).
            self.get_options_for_model(model)
            # Invalidate all submodels options and forget about
            # the model itself.
            for desc, desc_opts in list(self._registry.items()):
                if not issubclass(desc, model):
                    continue
                if model != desc and desc_opts.registered:
                    # Allowing to unregister a base would necessitate
                    # repatching all submodels.
                    raise DescendantRegistered(
                        'You need to unregister descendant "{}" before'
                        ' unregistering its base "{}"'.format(
                            desc.__name__, model.__name__
                        )
                    )
                del self._registry[desc]

    def get_registered_models(self, abstract=True):
        '''
        Returns a list of all registered models, or just concrete
        registered models.
        '''
        return [model for (model, opts) in self._registry.items()
                if opts.registered and (not model._meta.abstract or abstract)]

    def _get_options_for_model(self, model, opts_class=None, **options):
        '''
        Returns an instance of translation options with translated fields
        defined for the ``model`` and inherited from superclasses.
        '''
        if model not in self._registry:
            # Create a new type for backwards compatibility.
            opts = type('%sTranslationOptions' % model.__name__,
                        (opts_class or TranslationOptions,), options)(model)

            # Fields for translation may be inherited from abstract
            # superclasses, so we need to look at all parents.
            for base in model.__bases__:
                if not hasattr(base, '_meta'):
                    # Things without _meta aren't functional models, so they're
                    # uninteresting parents.
                    continue
                opts.update(self._get_options_for_model(base))

            # Cache options for all models -- we may want to compute options
            # of registered subclasses of unregistered models.
            self._registry[model] = opts

        return self._registry[model]

    def get_options_for_model(self, model):
        '''
        Thin wrapper around ``_get_options_for_model`` to preserve the
        semantic of throwing exception for models not directly registered.
        '''
        opts = self._get_options_for_model(model)
        if not opts.registered and not opts.related:
            raise NotRegistered(
                'The model "{}" is not registered for translation'.format(model.__name__)
            )
        return opts


# This global object represents the singleton translator object
translator = Translator()
