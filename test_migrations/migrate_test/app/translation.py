from modeltranslation.translator import TranslationOptions, translator

from .models import Blog, Category


class BlogTranslationOptions(TranslationOptions):
    fields = ("title", "body")


class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(Blog, BlogTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
