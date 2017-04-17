from modeltranslation2.translator import TranslationOptions, translator

from .models import Blog


class BlogTranslationOptions(TranslationOptions):
    fields = ('title', )

translator.register(Blog, BlogTranslationOptions)
