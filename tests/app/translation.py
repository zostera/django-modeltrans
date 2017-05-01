from modeltrans.translator import TranslationOptions, translator

from .models import Blog, Category, Person


# Models can be registered for translation like this.

class BlogTranslationOptions(TranslationOptions):
    fields = ('title', )
    required_languages = ('nl', )


class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', )


class PersonTranslationOptions(TranslationOptions):
    fields = ('occupation', )
    required_languages = ('en', 'nl')


translator.register(Blog, BlogTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(Person, PersonTranslationOptions)
