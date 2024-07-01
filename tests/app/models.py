from django.db import models
from django.utils.translation import gettext_lazy

from modeltrans.conf import get_default_language
from modeltrans.fields import TranslationField
from modeltrans.manager import MultilingualManager

try:
    from django.db.models import JSONField  # django==3.1 moved json field
except ImportError:
    from django.contrib.postgres.fields import JSONField


class CategoryQueryset(models.QuerySet):
    """
    Custom manager to make sure pickling on-the-fly created classes
    can be pickled, see test_querysets.py::PickleTest
    """


class Category(models.Model):
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    i18n = TranslationField(fields=("name", "title"))

    objects = CategoryQueryset.as_manager()

    def __str__(self):
        return self.name


class Site(models.Model):
    name = models.CharField(max_length=255)

    objects = MultilingualManager()

    def __str__(self):
        return self.name


class Blog(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)

    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.CASCADE)

    i18n = TranslationField(fields=("title", "body"), required_languages=("nl",))

    def __str__(self):
        return self.title


class TaggedBlog(models.Model):
    title = models.CharField(max_length=255)
    tags = JSONField(null=True, blank=True, default=list)

    i18n = TranslationField(fields=("title", "tags"))

    def __str__(self):
        return self.title


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    occupation = models.CharField(max_length=255)

    i18n = TranslationField(fields=("occupation",), required_languages=("en", "nl"))


class TextModel(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()

    i18n = TranslationField(fields=("title", "description"))

    def __str__(self):
        return self.title


class NullableTextModel(models.Model):
    description = models.TextField(null=True)

    i18n = TranslationField(fields=("description",))

    def __str__(self):
        return self.title


# copy of attributes in ringbase
class Attribute(models.Model):
    slug = models.SlugField(verbose_name="slug", unique=True)
    name = models.CharField("name", max_length=100, db_index=True)

    i18n = TranslationField(fields=("name",))

    def __str__(self):
        return self.name_i18n


class Choice(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField("value", max_length=100, blank=True, db_index=True)
    name = models.CharField("name", max_length=100, blank=True, db_index=True)
    description = models.TextField("description", blank=True)
    sort_order = models.IntegerField("sort order", default=0, db_index=True)

    i18n = TranslationField(fields=("name", "description"))


class AbstractBaseAttr(models.Model):
    """
    An abstract Base Class used to generate actual Attr classes
    """

    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = JSONField(null=True, blank=True)

    class Meta:
        abstract = True


def createBaseAttr(model):
    class GeneratedAttr(AbstractBaseAttr):
        """
        An abstract Base Class used to generate actual Attr classes
        with an object
        """

        object = models.ForeignKey(model, related_name="attrs", on_delete=models.CASCADE)

        _model = model

        class Meta:
            abstract = True
            unique_together = (("attribute", "object"),)

    return GeneratedAttr


class BlogAttr(createBaseAttr(Blog)):
    pass


class ArticleQueryset(models.QuerySet):
    pass


class AbstractArticle(models.Model):
    """
    Abstract Article with custom manger required
    to test patching of parent model managers.
    """

    title = models.CharField(max_length=255)

    i18n = TranslationField(fields=("title",))

    objects = ArticleQueryset.as_manager()

    class Meta:
        abstract = True


class Article(AbstractArticle):
    pass


class ChildArticle(Article):
    """
    Child Article for Django Models Inheritance testing
    """

    child_title = models.CharField(max_length=255)
    i18n_field_params = {"fields": ["title", "child_title"], "required_languages": ("nl",)}


class Challenge(models.Model):
    """Model using a custom fallback language per instance/record."""

    title = models.CharField(max_length=255)
    header = models.CharField(max_length=255, blank=True)

    default_language = models.CharField(
        max_length=2, null=True, blank=True, default=get_default_language()
    )

    i18n = TranslationField(fields=("title", "header"), fallback_language_field="default_language")

    def __str__(self):
        return self.title_i18n


class ChallengeContent(models.Model):
    """Model using a custom fallback language on a related record."""

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    content = models.TextField()

    i18n = TranslationField(
        fields=("content",), fallback_language_field="challenge__default_language"
    )

    def __str__(self):
        return self.content_i18n


class Post(models.Model):
    title = models.CharField(
        verbose_name=gettext_lazy("title of the post"),
        max_length=255,
    )
    is_published = models.BooleanField(default=False)

    i18n = TranslationField(fields=("title",))

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        limit_choices_to={"is_published": True},
        related_name="comments",
    )
    text = models.TextField()

    i18n = TranslationField(fields=("text",))

    def __str__(self):
        return self.text
