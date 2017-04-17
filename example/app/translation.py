from modeltranslation2.translator import TranslationOptions, translator

from .models import Blog, Category


# Models can be registered for translation like this.

class BlogTranslationOptions(TranslationOptions):
    fields = ('title', )


class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', )


translator.register(Blog, BlogTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
