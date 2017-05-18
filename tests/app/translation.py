from modeltrans.translator import TranslationOptions, translator

from .models import Attribute, Blog, Category, Choice, Person, TextModel


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


class AttributeTranslationOptions(TranslationOptions):
    fields = ('name', )


class ChoiceTranslationOptions(TranslationOptions):
    fields = ('name', 'description', )


translator.register(Attribute, AttributeTranslationOptions)
translator.register(Choice, ChoiceTranslationOptions)
