# -*- coding: utf-8 -*-
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Manager
from django.db.models.base import ModelBase
from django.utils.six import with_metaclass

from modeltrans import settings
from modeltrans.manager import MultilingualManager, MultilingualQuerysetManager

from .exceptions import AlreadyRegistered, DescendantRegistered, NotRegistered
from .fields import ActiveTranslationFieldProxy, TranslationFieldProxy
from .manager import transform_translatable_fields
# from .models import multilingual_getattr
from .utils import build_localized_fieldname


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

    def validate(self):
        '''
        Perform options validation.
        '''
        # TODO: at the moment only required_languages is validated.
        # Maybe check other options as well?
        if self.required_languages:
            if isinstance(self.required_languages, (tuple, list)):
                self._check_languages(self.required_languages)
            else:
                self._check_languages(self.required_languages.keys(), extra=('default',))
                for fieldnames in self.required_languages.values():
                    if any(f not in self.fields for f in fieldnames):
                        raise ImproperlyConfigured(
                            'Fieldname in required_languages which is not in fields option.')

    def _check_languages(self, languages, extra=()):
        correct = list(settings.AVAILABLE_LANGUAGES) + list(extra)
        if any(l not in correct for l in languages):
            raise ImproperlyConfigured(
                'Language in required_languages which is not in AVAILABLE_LANGUAGES.')

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
                    'Error adding translation field. Model "{}" already contains a field named "{}".'.format(
                        model._meta.object_name, field_name
                    )
                )


def add_translation_field(model, opts):
    '''
    Monkey patches the original model class to provide the `i18n` field.

    Adds newly created translation fields to the given translation options.
    '''
    # field to store the translations in
    model.add_to_class('i18n', JSONField(editable=False, null=True))

    # proxy fields to assign and get values from.
    for field_name in opts.local_fields.keys():

        # first, add a `<original_field>_i18n` proxy field to get the currently
        # active translation for a field
        active_translation_field = ActiveTranslationFieldProxy(model, field_name)
        i18n_field_name = build_localized_fieldname(field_name, 'i18n')
        raise_if_field_exists(model, i18n_field_name)

        setattr(model, i18n_field_name, active_translation_field)

        # now, for each language, add a proxy field to get the tranlation for
        # that langauge
        for language in list(settings.AVAILABLE_LANGUAGES) + [settings.DEFAULT_LANGUAGE, ]:
            translation_field = TranslationFieldProxy(
                original_field=field_name,
                model=model,
                language=language
            )
            localized_field_name = translation_field.get_field_name()

            raise_if_field_exists(model, localized_field_name)

            setattr(model, localized_field_name, translation_field)
            opts.add_translation_field(field_name, translation_field)


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
            class NewMultilingualManager(MultilingualManager, manager.__class__,
                                         MultilingualQuerysetManager):
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


def patch_clean_fields(model):
    '''
    Patch clean_fields method to handle different form types submission.
    '''
    old_clean_fields = model.clean_fields

    def new_clean_fields(self, exclude=None):
        if hasattr(self, '_mt_form_pending_clear'):
            # Some form translation fields has been marked as clearing value.
            # Check if corresponding translated field was also saved (not excluded):
            # - if yes, it seems like form for MT-unaware app. Ignore clearing (left value from
            #   translated field unchanged), as if field was omitted from form
            # - if no, then proceed as normally: clear the field
            for field_name, value in self._mt_form_pending_clear.items():
                field = self._meta.get_field(field_name)
                orig_field_name = field.translated_field.name
                if orig_field_name in exclude:
                    field.save_form_data(self, value, check=False)
            delattr(self, '_mt_form_pending_clear')
        old_clean_fields(self, exclude)
    model.clean_fields = new_clean_fields


def patch_metaclass(model):
    '''
    Monkey patches original model metaclass to exclude translated fields on deferred subclasses.
    '''
    old_mcs = model.__class__

    class translation_deferred_mcs(old_mcs):
        '''
        This metaclass is essential for deferred subclasses (obtained via
        only/defer) to work.

        When deferred subclass is created, some translated fields descriptors
        could be overridden by `DeferredAttribute` - which would cause
        translation retrieval to fail. Prevent this from happening with deleting
        those attributes from class being created. This metaclass would be
        called from django.db.models.query_utils.deferred_class_factory
        '''
        def __new__(cls, name, bases, attrs):
            if attrs.get('_deferred', False):
                opts = translator.get_options_for_model(model)
                were_deferred = set()
                for field_name in opts.fields.keys():
                    if attrs.pop(field_name, None):
                        # Field was deferred. Store this for future reference.
                        were_deferred.add(field_name)
                if len(were_deferred):
                    attrs['_fields_were_deferred'] = were_deferred
            return super(translation_deferred_mcs, cls).__new__(cls, name, bases, attrs)
    # Assign to __metaclass__ wouldn't work, since metaclass search algorithm check for __class__.
    # http://docs.python.org/2/reference/datamodel.html#__metaclass__
    model.__class__ = translation_deferred_mcs


def delete_cache_fields(model):
    opts = model._meta
    cached_attrs = ('_field_cache', '_field_name_cache', '_name_map', 'fields', 'concrete_fields',
                    'local_concrete_fields')
    for attr in cached_attrs:
        try:
            delattr(opts, attr)
        except AttributeError:
            pass

    if hasattr(model._meta, '_expire_cache'):
        model._meta._expire_cache()


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
        opts.validate()

        # Mark the object explicitly as registered -- registry caches
        # options of all models, registered or not.
        opts.registered = True

        # Add translation fields to the model.
        if model._meta.proxy:
            delete_cache_fields(model)
        else:
            add_translation_field(model, opts)

        # Delete all fields cache for related model (parent and children)
        related = ((
            f for f in model._meta.get_fields()
            if (f.one_to_many or f.one_to_one) and
            f.auto_created
        ))

        for related_obj in related:
            delete_cache_fields(related_obj.model)

        # Set MultilingualManager
        add_manager(model)

        # Patch __init__ to rewrite fields
        patch_constructor(model)

        # Patch clean_fields to verify form field clearing
        patch_clean_fields(model)

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
