from modeltrans.translator import TranslationOptions, translator

from .models import Blog, Category, Person, TextModel


# Models can be registered for translation like this.

class BlogTranslationOptions(TranslationOptions):
    fields = ('title', )
    required_languages = ('nl', )


class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', )


class PersonTranslationOptions(TranslationOptions):
    fields = ('occupation', )
    required_languages = ('en', 'nl')


class TextModelTranslationOptions(TranslationOptions):
    fields = ('title', 'description', )


translator.register(Blog, BlogTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(Person, PersonTranslationOptions)
translator.register(TextModel, TextModelTranslationOptions)
