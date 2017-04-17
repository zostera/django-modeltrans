from modeltranslation2.translator import TranslationOptions, translator

from .models import Blog


# Models can be registered for translation like this.

class BlogTranslationOptions(TranslationOptions):
    fields = ('title', )

translator.register(Blog, BlogTranslationOptions)
