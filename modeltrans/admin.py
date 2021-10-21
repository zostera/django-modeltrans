from .forms import TranslationModelForm


class ActiveLanguageMixin:
    """
    ModelAdmin mixin to only show fields for the fallback and current language in the change view.
    """

    form_class = TranslationModelForm
