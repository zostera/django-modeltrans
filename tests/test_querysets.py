import pickle
from unittest import skipIf

import django
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Collate
from django.test import TestCase, override_settings
from django.utils.translation import override

from modeltrans.fields import TranslationField
from modeltrans.translator import translate_model

from .app.models import Attribute, Blog, BlogAttr, Category, Challenge, ChallengeContent, Site
from .utils import CreateTestModel, load_wiki


def key(queryset, key, sep=" "):
    items = list([getattr(model, key) for model in queryset])
    if sep is not None:
        items = sep.join(items)
    return items


class GetFieldTest(TestCase):
    """
    Test getting from a lookup to a field.
    """

    def assert_lookup(self, lookup, expected_fieldname, expected_lookup_type=None):
        field, lookup_type = Blog.objects.all()._get_field(lookup)

        self.assertEqual(field.name, expected_fieldname)
        self.assertEqual(lookup_type, expected_lookup_type)

    def test_pk(self):
        self.assert_lookup("pk", "id")

    def test_non_id_pk(self):
        """This model doesn't have a id column"""

        class NonIdPrimaryKeyModel(models.Model):
            slug = models.SlugField(primary_key=True)
            title = models.CharField(max_length=100)
            i18n = TranslationField(fields=("title",))

            class Meta:
                app_label = "tests"

        translate_model(NonIdPrimaryKeyModel)

        with CreateTestModel(NonIdPrimaryKeyModel):
            field, lookup_type = NonIdPrimaryKeyModel.objects.all()._get_field("pk")

            self.assertEqual(field.name, "slug")

    def test_bare_field(self):
        self.assert_lookup("title", "title")
        self.assert_lookup("title_nl", "title_nl")
        self.assert_lookup("category__name", "name")

    def test_contains(self):
        self.assert_lookup("title__contains", "title", "contains")
        self.assert_lookup("title_nl__contains", "title_nl", "contains")
        self.assert_lookup("category__name__contains", "name", "contains")

    def test_endswith(self):
        self.assert_lookup("title__endswith", "title", "endswith")
        self.assert_lookup("category__name__endswith", "name", "endswith")

    def test_lower_endswith(self):
        self.assert_lookup("title__lower__endswith", "title", "lower__endswith")
        self.assert_lookup("category__name__lower__endswith", "name", "lower__endswith")


class PickleTest(TestCase):
    @classmethod
    def setUpTestData(self):
        c = Category.objects.create(name="Hobby")
        Blog.objects.create(title="Pickle", title_de="Einlegen", title_nl="Inmaken", category=c)
        Blog.objects.create(
            title="Roadcycling", title_de="Radfahren", title_nl="Racefietsen", category=c
        )

    def test_pickle_queryset(self):
        qs = Blog.objects.all()
        serialized = pickle.dumps(qs)

        self.assertEqual({m.title for m in qs}, {m.title for m in pickle.loads(serialized)})

    def test_pickle_prefetch_related(self):
        qs = Blog.objects.all().prefetch_related("category")
        serialized = pickle.dumps(qs)

        self.assertEqual({m.title for m in qs}, {m.title for m in pickle.loads(serialized)})

    def test_pickle_custom_queryset(self):
        qs = Category.objects.all()
        serialized = pickle.dumps(qs)

        self.assertEqual({m.name for m in qs}, {m.name for m in pickle.loads(serialized)})


class FilterTest(TestCase):
    data = (
        ("Falcon", "Valk", "Birds"),
        ("Frog", "Kikker", None),
        ("Toad", "Pad", None),
        ("Duck", "Eend", "Birds"),
        ("Dolphin", "Dolfijn", None),
    )

    @classmethod
    def setUpTestData(self):
        birds = Category.objects.create(name="Birds", name_nl="Vogels")

        for title, title_nl, category in FilterTest.data:
            b = Blog.objects.create(title=title, i18n={"title_nl": title_nl})
            if category == birds.name:
                b.category = birds
                b.save()

    def test_filter_contains(self):
        """
        We want to do a text contains in translated value lookup
        """
        qs = Blog.objects.filter(title_nl__contains="al")
        self.assertEqual(qs[0].title_nl, "Valk")

        qs = Blog.objects.filter(title__contains="al")
        self.assertEqual(qs[0].title, "Falcon")

    def test_filter_exact(self):
        qs = Blog.objects.filter(title_nl="Valk")
        self.assertEqual(qs[0].title, "Falcon")

        qs = Blog.objects.filter(title="Falcon")
        self.assertEqual(qs[0].title, "Falcon")

    def test_filter_startswith(self):
        qs = Blog.objects.filter(title_nl__startswith="Va")
        self.assertEqual(qs[0].title, "Falcon")

    def test_exclude_exact(self):
        expected = {"Frog", "Toad", "Duck", "Dolphin"}

        qs = Blog.objects.exclude(title="Falcon")
        self.assertEqual({m.title for m in qs}, expected)

        qs = Blog.objects.exclude(title_nl="Valk")
        self.assertEqual({m.title for m in qs}, expected)

        qs = Blog.objects.exclude(title_nl="Valk").exclude(title_nl="Pad")
        self.assertEqual({m.title for m in qs}, {"Frog", "Duck", "Dolphin"})

    def test_exclude_contains(self):
        qs = Blog.objects.exclude(title_nl__contains="o")
        self.assertEqual({m.title for m in qs}, {"Falcon", "Frog", "Toad", "Duck"})

    def test_filter_i18n(self):
        Blog.objects.create(title="Cod")

        with override("nl"):
            # should fallback to english
            qs = Blog.objects.filter(title_i18n="Cod")
            self.assertEqual({m.title for m in qs}, {"Cod"})

            # should not fallback
            qs = Blog.objects.filter(title_nl="Cod")
            self.assertEqual({m.title for m in qs}, set())

    def test_filter_by_default_language(self):
        qs = Blog.objects.filter(title_en__contains="al")
        self.assertEqual({m.title for m in qs}, {"Falcon"})
        self.assertTrue("annotation" not in str(qs.query))

    def test_get(self):
        """get() is just a special case of filter()"""
        b = Blog.objects.get(title_nl="Valk")

        self.assertEqual(b.title, "Falcon")

        with self.assertRaisesMessage(Blog.DoesNotExist, "Blog matching query does not exist."):
            Blog.objects.get(title_fr="Boo")

    def test_filter_Q_object(self):
        b = Blog.objects.get(Q(title_nl__contains="al"))
        self.assertEqual(b.title, "Falcon")

        b = Blog.objects.get(Q(title_en__contains="Fro"))
        self.assertEqual(b.title, "Frog")

        qs = Blog.objects.filter(Q(title_nl__contains="al") | Q(title_en__contains="Fro"))
        self.assertEqual({m.title for m in qs}, {"Falcon", "Frog"})

        b = Blog.objects.get(Q(title_nl__contains="al"), Q(title_en__contains="al"))
        self.assertEqual(b.title, "Falcon")

        with override("nl"):
            b = Blog.objects.get(Q(title_i18n="Kikker"))
            self.assertEqual(b.title, "Frog")

    def test_filter_F_expression(self):
        Blog.objects.create(title="foo", title_nl=20, title_fr=10)
        Blog.objects.create(title="bar", title_nl=20, title_fr=30)
        Blog.objects.create(title="baz", title_nl=20, title_fr=40)

        qs = Blog.objects.filter(title_nl__gt=F("title_fr"))
        self.assertEqual({m.title for m in qs}, {"foo"})

        qs = Blog.objects.filter(title_nl__lt=F("title_fr"))
        self.assertEqual({m.title for m in qs}, {"bar", "baz"})

    def test_filter_F_expressions_function(self):
        Blog.objects.create(title="foo", title_nl="foo")
        Blog.objects.create(title="bar", title_nl="BAR")
        Blog.objects.create(title="baz", title_nl="BAZ")

        qs = Blog.objects.filter(title_nl=models.functions.Upper(F("title_nl")))
        self.assertEqual({m.title for m in qs}, {"bar", "baz"})

    def test_filter_relations(self):
        mass = Attribute.objects.create(slug="mass", name="Mean Mass")
        length = Attribute.objects.create(slug="length", name="Length", name_nl="Lengte")

        dog = Blog.objects.create(title="Australian Kelpie Dog")
        whale = Blog.objects.create(title="Blue Whale", title_nl="Blauwe vinvis")

        BlogAttr.objects.create(object=dog, attribute=mass, value=17)
        BlogAttr.objects.create(object=dog, attribute=length, value=0.50)
        BlogAttr.objects.create(object=whale, attribute=mass, value=181000)
        BlogAttr.objects.create(object=whale, attribute=length, value=28)

        with override("nl"):
            Attribute.objects.filter(
                blogattr__object_id__in=Blog.objects.filter(title__contains="al")
            )

    def test_filter_subquery(self):
        """
        When in a subquery, the table alias should be used rather than the real
        table name.
        """
        c1 = Category.objects.create(name="Sofa", name_nl="Bank")
        c2 = Category.objects.create(name="modeltrans", name_nl="modeltrans")
        birds = Category.objects.create(name="Birds")

        Blog.objects.create(title="Chesterfield", category=c1)
        Blog.objects.create(title="Why migrate", category=c2)
        Blog.objects.create(title="Initial prototype", category=c2)
        Blog.objects.create(title="Dogfooding", category=c2)

        Blog.objects.create(title="Falcon", category=birds)

        qs = Blog.objects.filter(category__in=Category.objects.filter(name_nl__contains="an"))
        self.assertEqual(
            {m.title_i18n for m in qs},
            {"Chesterfield", "Why migrate", "Initial prototype", "Dogfooding"},
        )

    def test_queryset_related_model(self):
        qs = Blog.objects.filter(category__name_nl="Vogels")
        self.assertEqual({m.title for m in qs}, {"Falcon", "Duck"})

    def test_filter_spanning_relation(self):
        birds = Category.objects.get(name="Birds")
        bird_blogs = Blog.objects.filter(category=birds)

        self.assertEqual(
            {b.title for b in Blog.objects.filter(category__name_nl="Vogels")},
            {b.title for b in bird_blogs},
        )

    def test_filter_spanning_relation_from_non_translatable(self):
        """
        `MultilingualManager` must be set on non-translated models too in order
        to use the rewrite of the fields.
        """
        s = Site.objects.create(name="Testsite")
        Blog.objects.create(title="Strange", title_nl="Vreemd", site=s)

        site_modeltrans = Site.objects.create(name="Modeltrans blog")
        Blog.objects.create(title="Version 0.1.1 of modeltrans released", site=site_modeltrans)

        qs = Site.objects.filter(blog__title="Strange")
        self.assertEqual({m.name for m in qs}, {"Testsite"})

        qs = Site.objects.filter(blog__title_nl="Vreemd")
        self.assertEqual({m.name for m in qs}, {"Testsite"})

        qs = Site.objects.filter(blog__title_i18n__contains="modeltrans")
        self.assertEqual({m.name for m in qs}, {"Modeltrans blog"})


class CustomFallbackTest(TestCase):
    def test_custom_fallback(self):
        instance = Challenge.objects.create(
            default_language="nl", title="Hurray", i18n={"title_nl": "Hoera"}
        )

        with override("de"):
            self.assertCountEqual(Challenge.objects.filter(title_i18n="Hoera"), [instance])
        with override("nl"):
            self.assertCountEqual(Challenge.objects.filter(title_i18n="Hoera"), [instance])
        with override("en"):
            self.assertCountEqual(Challenge.objects.filter(title_i18n="Hoera"), [])

    def test_custom_fallback_null(self):
        instance = Challenge.objects.create(
            default_language=None, title="Hurray", i18n={"title_nl": "Hoera"}
        )
        with override("de"):
            self.assertCountEqual(Challenge.objects.filter(title_i18n="Hoera"), [])
        with override("nl"):
            self.assertCountEqual(Challenge.objects.filter(title_i18n="Hoera"), [instance])
        with override("en"):
            self.assertCountEqual(Challenge.objects.filter(title_i18n="Hoera"), [])

    def test_custom_fallback_follow_relation(self):
        challenge = Challenge.objects.create(default_language="nl", title="Hurray")
        content = ChallengeContent.objects.create(
            challenge=challenge, content="Congratulations", i18n={"content_nl": "Gefeliciteerd"}
        )
        with override("de"):
            self.assertCountEqual(
                ChallengeContent.objects.filter(content_i18n="Gefeliciteerd"), [content]
            )
        with override("nl"):
            self.assertCountEqual(
                ChallengeContent.objects.filter(content_i18n="Gefeliciteerd"), [content]
            )
        with override("en"):
            self.assertCountEqual(ChallengeContent.objects.filter(content_i18n="Gefeliciteerd"), [])


class FulltextSearch(TestCase):
    def test_SearchVector(self):
        load_wiki()

        from django.contrib.postgres.search import SearchVector

        qs = Blog.objects.annotate(search=SearchVector("title_i18n", "body_i18n")).filter(
            search="prey"
        )
        self.assertEqual({m.title for m in qs}, {"Vulture", "Falcon", "Dolphin"})


class SimpleOrderByTest(TestCase):
    EN = ["A", "B", "C", "D", "E", "F", "G"]
    NL = ["A", "B", "C", "D", "Z", "Y", "X"]
    FR = ["1", "1", "1", "1", "2", "2", "2"]

    @classmethod
    def setUpTestData(self):
        for i, en in enumerate(self.EN):
            Blog.objects.create(title=en, i18n={"title_nl": self.NL[i], "title_fr": self.FR[i]})

    def test_regular_fields(self):
        qs = Blog.objects.all().order_by("-title")

        self.assertEqual(key(qs, "title"), "G F E D C B A")

    def test_order_by_two_fields(self):
        """Multiple translated fields should work too"""
        qs = Blog.objects.all().order_by("-title_fr", "title_nl")

        self.assertEqual(key(qs, "title_nl"), "X Y Z A B C D")

    def test_order_asc(self):
        qs = Blog.objects.all().order_by("title_nl")

        self.assertEqual(key(qs, "title_nl"), "A B C D X Y Z")
        self.assertEqual(key(qs, "title"), "A B C D G F E")

    def test_order_desc(self):
        qs = Blog.objects.all().order_by("-title_nl")
        self.assertEqual(key(qs, "title_nl"), "Z Y X D C B A")

        qs = Blog.objects.all().order_by("-title")
        self.assertEqual(key(qs, "title"), "G F E D C B A")

    def test_order_by_i18n(self):
        Blog.objects.create(title="H")
        with override("nl"):
            qs = Blog.objects.all().order_by("title_i18n")

            self.assertEqual(key(qs, "title_i18n"), "A B C D H X Y Z")


class AnnotateTest(TestCase):
    @classmethod
    def setUpTestData(self):
        birds = Category.objects.create(name="Birds", name_nl="Vogels")
        mammals = Category.objects.create(name="Mammals", name_nl="Zoogdieren")

        Blog.objects.bulk_create(
            [
                Blog(title="Falcon", title_nl="Valk", category=birds),
                Blog(title="Vulture", category=birds),
                Blog(title="Bat", category=mammals),
                Blog(title="Dolfin", category=mammals),
                Blog(title="Zebra", title_nl="Zebra", category=mammals),
            ]
        )

    def test_annotate_normal_count(self):
        qs = Category.objects.annotate(num_blogs=models.Count("blog__title"))

        self.assertEqual({(m.name, m.num_blogs) for m in qs}, {("Mammals", 3), ("Birds", 2)})

    # def test_more_complex_counts(self):

    def test_annotate_count_i18n_field(self):
        qs = Category.objects.annotate(num_blogs=models.Count("blog__title_nl"))

        self.assertEqual({(m.name, m.num_blogs) for m in qs}, {("Mammals", 1), ("Birds", 1)})

    def test_annotate_coalesce(self):
        qs = Blog.objects.annotate(e=models.functions.Coalesce("title_nl", models.Value("EMPTY")))
        self.assertEqual(key(qs, "e"), "Valk EMPTY EMPTY EMPTY Zebra")

    def test_annotate_substr(self):
        qs = Blog.objects.annotate(e=models.functions.Substr("title_nl", 1, 3))

        self.assertEqual(list(qs.values_list("e", flat=True)), ["Val", None, None, None, "Zeb"])

    def test_annotate_upper(self):
        with override("nl"):
            qs = Blog.objects.annotate(e=models.functions.Upper("title_i18n"))

            self.assertEqual(key(qs, "e"), "VALK VULTURE BAT DOLFIN ZEBRA")

    def test_annotate_length(self):
        with override("nl"):
            qs = Blog.objects.annotate(len=models.functions.Length("title_i18n"))

            self.assertEqual(
                list(qs.values_list("len", flat=True)),
                list(map(len, ["VALK", "VULTURE", "BAT", "DOLFIN", "ZEBRA"])),
            )

    def test_annotate_with_some_expressions(self):
        Blog.objects.create(category=Category.objects.get(name="Birds"), title_nl="Gull")
        qs = Category.objects.annotate(
            a=models.Count("blog__title_nl") + 1,
            b=1 + models.Count("blog__title_nl"),
            c=1 / models.Count("blog__title_nl"),
            d=4 * models.Count("blog__title_nl"),
        )

        self.assertEqual(
            set(qs.values_list("name", "a", "b", "c", "d")),
            {("Birds", 3, 3, 0, 8), ("Mammals", 2, 2, 1, 4)},
        )


class OrderByTest(TestCase):
    @classmethod
    def setUpTestData(self):
        birds = Category.objects.create(name="Birds", name_nl="Vogels")
        mammals = Category.objects.create(name="Mammals", name_nl="Zoogdieren")

        Blog.objects.bulk_create(
            [
                Blog(title="Falcon", title_nl="Valk", category=birds),
                Blog(title="Vulture", title_nl="Gier", category=birds),
                Blog(title="Bat", category=mammals),
                Blog(title="Dolfin", category=mammals),
                Blog(title="Zebra", category=mammals),
            ]
        )

    def test_order_by_related_field(self):
        expected = "Zebra Dolfin Bat Vulture Falcon"
        qs = Blog.objects.filter(category__isnull=False).order_by("-category__name_i18n", "-title")
        self.assertEqual(key(qs, "title"), expected)

        qs = Blog.objects.filter(category__isnull=False).order_by("-category__name_nl", "-title")
        self.assertEqual(key(qs, "title"), expected)

    def test_order_by_lower(self):
        """
        Beware: database configuration influences ordering.
        """
        from django.db.models.functions import Lower

        c = Category.objects.create(name="test")
        Blog.objects.create(title="A", title_nl="c", category=c)
        Blog.objects.create(title="a", title_nl="b", category=c)

        filtered = Blog.objects.filter(category=c)

        # order by title should result in Aa because it is case sensitive.
        qs = filtered.order_by(Collate("title", "C"), Collate("title_nl", "C"))
        self.assertEqual(key(qs, "title"), "A a")

        # order by Lower('title') should result in Aa because lower('A') == lower('A')
        # so the title_nl field should determine the sorting
        qs = filtered.order_by(Lower("title"), "title_nl")
        self.assertEqual(key(qs, "title"), "a A")

        # applying lower to title_nl should not matter since it is not the same letter
        qs = filtered.order_by(Lower("title_nl"))
        self.assertEqual(key(qs, "title"), "a A")

        # should be the same as previous
        with override("nl"):
            qs = filtered.order_by(Lower("title_i18n"))
            self.assertEqual(key(qs, "title"), "a A")

    def test_order_by_two_virtual_fields(self):
        ca = Category.objects.create(name="foo a", title="test a", title_nl="testje a")
        cb = Category.objects.create(name="foo b", title="test b", title_nl="testje b")

        Blog.objects.bulk_create(
            [
                Blog(title="a", title_nl="d", category=cb),
                Blog(title="b", title_nl="c", category=cb),
                Blog(title="c", title_nl="b", category=cb),
                Blog(title="z", title_nl="a", category=ca),
                Blog(title="y", title_nl="b", category=ca),
                Blog(title="x", title_nl="c", category=ca),
            ]
        )

        qs = Blog.objects.filter(category__title_nl__contains="test").order_by(
            "-category__title_nl", "-title_nl"
        )
        self.assertEqual(key(qs, "title"), "a b c x y z")

    def test_order_by_annotation(self):
        qs = Category.objects.annotate(num_blogs=models.Count("blog__title"))

        self.assertEqual(key(qs.order_by("num_blogs"), "name"), "Birds Mammals")
        self.assertEqual(key(qs.order_by("-num_blogs"), "name"), "Mammals Birds")

    def test_order_by_expression(self):
        qs = Category.objects.order_by(F("name_i18n").desc())

        self.assertEqual(key(qs, "name"), "Mammals Birds")

    def test_order_by_textfield(self):
        Blog.objects.create(title="Wolf", body="Wolf print found in dirtroad")
        Blog.objects.create(title="Wolf2", body="A Wolf print found in dirtroad")

        with override("nl"):
            qs = Blog.objects.filter(body_i18n__contains="olf").order_by("-body")

            self.assertEqual(key(qs, "title"), "Wolf Wolf2")

    @skipIf(True, "Needs a solution")
    def test_order_by_distinct(self):
        """
        Postgres requires the distict expression to match the order_by expression.
        This is because it needs to reliably choose the first row from a set of
        duplicates, which is only possible if the results are also ordered by the
        value that needs to be distinct.

        https://github.com/zostera/django-modeltrans/issues/27

        The english case works, as the queryset is sorted on `title_i18n`, which is
        translated to `title`.

        For the dutch case, this error message is raised, because `title_i18n`
        translates to a COALESCE-expression, resulting in a database error:

        SELECT DISTINCT ON expressions must match initial ORDER BY expressions.
        """

        with override("en"):
            qs = (
                Blog.objects.filter(category__name_i18n="Birds")
                .order_by("title_i18n")
                .distinct("title")
            )
            self.assertEqual(key(qs, "title_i18n"), "Falcon Vulture")

        with override("nl"):
            qs = (
                Blog.objects.filter(category__name_i18n="Vogels")
                .order_by("title_i18n")
                .distinct("title_i18n")
            )
            self.assertEqual(key(qs, "title_i18n"), "Valk Gier")


class FallbackOrderByTest(TestCase):
    @override_settings(
        MODELTRANS_AVAILABLE_LANGUAGES=("fr", "fy", "nl"),
        MODELTRANS_FALLBACK={"default": ("en",), "fy": ("nl", "en")},
        DEBUG=True,
    )
    def test_order_by_fallback_chain(self):
        class TestObj(models.Model):
            title = models.CharField(max_length=100)
            i18n = TranslationField(fields=("title",))

            class Meta:
                app_label = "tests"

        translate_model(TestObj)

        with CreateTestModel(TestObj):
            TestObj.objects.bulk_create(
                [
                    TestObj(title="Falcon", title_nl="Valk"),
                    TestObj(
                        title="Frog", title_nl="Kikker", title_fr="Grenouilles", title_fy="Frosk"
                    ),
                    TestObj(title="Fox", title_nl="Vos", title_fy="Foks"),
                    TestObj(title="Gecko"),
                    TestObj(title="Gerbil"),
                    TestObj(title="Vulture", title_nl="Gier", title_fr="Vautour"),
                ]
            )

            # should use the 'default' fallback chain
            with override("nl"):
                qs = TestObj.objects.all().order_by("title_i18n")
                self.assertEqual(key(qs, "title_i18n"), "Gecko Gerbil Gier Kikker Valk Vos")

            # should use the 'fy' fallback chain
            with override("fy"):
                qs = TestObj.objects.all().order_by("title_i18n")
                self.assertEqual(key(qs, "title_i18n"), "Foks Frosk Gecko Gerbil Gier Valk")

                qs = TestObj.objects.all().order_by("-title_i18n")
                self.assertEqual(key(qs, "title_i18n"), "Valk Gier Gerbil Gecko Frosk Foks")

            # should use the 'default' fallback chain
            with override("fr"):
                qs = TestObj.objects.all().order_by("title_i18n")
                self.assertEqual(
                    key(qs, "title_i18n"), "Falcon Fox Gecko Gerbil Grenouilles Vautour"
                )


class FilteredOrderByTest(TestCase):
    def test_filtered_order_by(self):
        Blog.objects.bulk_create(
            [
                Blog(title="Falcon", title_nl="Valk"),
                Blog(title="Frog", title_nl="Kikker"),
                Blog(title="Fox", title_nl="Vos"),
                Blog(title="Gecko"),
                Blog(title="Gerbil"),
                Blog(title="Vulture", title_nl="Gier"),
            ]
        )

        qs = Blog.objects.filter(title_en__contains="F").order_by("title_nl")
        self.assertEqual(key(qs, "title_nl"), "Kikker Valk Vos")

        qs = Blog.objects.filter(title_en__contains="G").order_by("title_en")
        self.assertEqual(key(qs, "title"), "Gecko Gerbil")

        with override("nl"):
            qs = Blog.objects.filter(title_i18n__contains="G").order_by("title_i18n")
            self.assertEqual(key(qs, "title_i18n"), "Gecko Gerbil Gier")

        with override("en"):
            qs = Blog.objects.filter(title_i18n__contains="G").order_by("-title_i18n")

            self.assertEqual(key(qs, "title_i18n"), "Gerbil Gecko")
            self.assertTrue("annotation" not in str(qs.query))


@skipIf(django.VERSION < (2, 0), "Only supported in Django 2.0 and later")
class ModelMetaOrderByTest(TestCase):
    def test_meta_ordering(self):
        """
        This needs expressions in Model.Meta.ordering, added in django 2.0
        https://github.com/django/django/pull/8673
        """

        class MetaOrderingModel(models.Model):
            # doesn't make sense to translate names, but it serves as a test.
            first_name = models.CharField(max_length=100)
            last_name = models.CharField(max_length=100)

            i18n = TranslationField(fields=("last_name", "first_name"))

            class Meta:
                ordering = ("last_name_i18n", "first_name_i18n")
                app_label = "tests"

        TEST_NAMES = (
            ("Jaïr", "Kleinsma"),
            ("Hakki", "van Velsen"),
            ("Josip", "Engel"),
            ("Berry", "Reuver"),
        )

        translate_model(MetaOrderingModel)
        with CreateTestModel(MetaOrderingModel):
            for first, last in TEST_NAMES:
                MetaOrderingModel.objects.create(first_name=first, last_name=last)

            qs = MetaOrderingModel.objects.all()
            self.assertEqual(key(qs, "first_name"), "Josip Jaïr Berry Hakki")

            # overridden:
            self.assertEqual(key(qs.order_by("first_name"), "first_name"), "Berry Hakki Jaïr Josip")


class ValuesTest(TestCase):
    def setUp(self):
        birds = Category.objects.create(name="Birds", name_nl="Vogels")
        amphibians = Category.objects.create(name="Amphibians", name_nl="Amfibiën")
        reptiles = Category.objects.create(name="Reptiles")

        Blog.objects.bulk_create(
            [
                Blog(title="Falcon", title_nl="Valk", category=birds),
                Blog(title="Frog", title_nl="Kikker", category=amphibians),
                Blog(title="Gecko", category=reptiles),
            ]
        )

    def assertEqualsList(self, qs, expected):
        try:
            self.assertEqual(list(qs), expected)
        except AssertionError:
            print("Queryset query: {}".format(qs.query))

            raise

    def test_queryset_values_basic(self):
        self.assertEqualsList(
            Blog.objects.all().order_by("title_nl").values("title_nl"),
            [{"title_nl": None}, {"title_nl": "Kikker"}, {"title_nl": "Valk"}],
        )

    def test_queryset_values_default_language(self):
        self.assertEqualsList(
            Blog.objects.all().order_by("title_en").values("title_en"),
            [{"title_en": "Falcon"}, {"title_en": "Frog"}, {"title_en": "Gecko"}],
        )

    def test_queryset_values_i18n(self):
        with override("nl"):
            self.assertEqualsList(
                Blog.objects.all().order_by("title_i18n").values("title_i18n"),
                [{"title_i18n": "Gecko"}, {"title_i18n": "Kikker"}, {"title_i18n": "Valk"}],
            )

    def test_queryset_values_list(self):
        # doesn't make sense to add a much tests for values_list() specifically,
        # as the underlying function for value() is axactly the same.
        qs = Blog.objects.all().order_by("title_nl").values_list("title_nl")
        self.assertEqual(list(qs), [(None,), ("Kikker",), ("Valk",)])

    def test_queryset_values_list_default_language(self):
        self.assertEqual(
            list(Blog.objects.all().order_by("title_en").values_list("title_en")),
            list(Blog.objects.all().order_by("title").values_list("title")),
        )

    def test_queryset_related_model(self):
        self.assertEqualsList(
            Blog.objects.all().values_list("title_i18n", "category__name_i18n"),
            [("Falcon", "Birds"), ("Frog", "Amphibians"), ("Gecko", "Reptiles")],
        )

    def test_values_kwarg_lower(self):
        from django.db.models.functions import Lower

        qs1 = Blog.objects.values(lower_name=Lower("category__name"))
        qs2 = Blog.objects.values(lower_name=Lower("category__name_en"))
        self.assertEqual(list(qs1), list(qs2))

    def test_values_spanning_relation(self):
        qs = Blog.objects.all().order_by("title_nl").values_list("title_nl", "category__name_nl")
        self.assertEqual(list(qs), [(None, None), ("Kikker", "Amfibiën"), ("Valk", "Vogels")])
