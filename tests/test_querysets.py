# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import skip

from django.db import models
from django.db.models import F, Q
from django.test import TestCase, override_settings
from django.utils.translation import override

from modeltrans.fields import TranslationField
from modeltrans.translator import translate_model

from .app.models import Attribute, Blog, BlogAttr, Category, Choice, Site
from .utils import CreateTestModel


def key(queryset, key):
    return list([getattr(model, key) for model in queryset])


class GetFieldTest(TestCase):
    '''
    Test getting from a lookup to a field.
    '''
    def assert_lookup(self, lookup, expected_fieldname, expected_lookup_type=''):
        field, lookup_type = Blog.objects.all()._get_field(lookup)

        self.assertEquals(field.name, expected_fieldname)
        self.assertEquals(lookup_type, expected_lookup_type)

    def test_bare_field(self):
        self.assert_lookup('title', 'title')
        self.assert_lookup('title_nl', 'title_nl')
        self.assert_lookup('category__name', 'name')

    def test_contains(self):
        self.assert_lookup('title__contains', 'title', 'contains')
        self.assert_lookup('title_nl__contains', 'title_nl', 'contains')
        self.assert_lookup('category__name__contains', 'name', 'contains')

    def test_endswith(self):
        self.assert_lookup('title__endswith', 'title', 'endswith')
        self.assert_lookup('category__name__endswith', 'name', 'endswith')


class FilterTest(TestCase):
    data = (
        ('Falcon', 'Valk', 'Birds'),
        ('Frog', 'Kikker', None),
        ('Toad', 'Pad', None),
        ('Duck', 'Eend', 'Birds'),
        ('Dolphin', 'Dolfijn', None)
    )

    def setUp(self):
        birds = Category.objects.create(name='Birds', name_nl='Vogels')

        for title, title_nl, category in self.data:
            b = Blog.objects.create(title=title, i18n={'title_nl': title_nl})
            if category == birds.name:
                b.category = birds
                b.save()

    def test_filter_contains(self):
        '''
        We want to do a text contains in translated value lookup
        '''
        qs = Blog.objects.filter(title_nl__contains='al')
        self.assertEquals(qs[0].title_nl, 'Valk')

        qs = Blog.objects.filter(title__contains='al')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_filter_exact(self):
        qs = Blog.objects.filter(title_nl='Valk')
        self.assertEquals(qs[0].title, 'Falcon')

        qs = Blog.objects.filter(title='Falcon')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_filter_startswith(self):
        qs = Blog.objects.filter(title_nl__startswith='Va')
        self.assertEquals(qs[0].title, 'Falcon')

    def test_exclude_exact(self):
        expected = {'Frog', 'Toad', 'Duck', 'Dolphin'}

        qs = Blog.objects.exclude(title='Falcon')
        self.assertEquals({m.title for m in qs}, expected)

        qs = Blog.objects.exclude(title_nl='Valk')
        self.assertEquals({m.title for m in qs}, expected)

        qs = Blog.objects.exclude(title_nl='Valk').exclude(title_nl='Pad')
        self.assertEquals({m.title for m in qs}, {'Frog', 'Duck', 'Dolphin'})

    def test_exclude_contains(self):
        qs = Blog.objects.exclude(title_nl__contains='o')
        self.assertEquals({m.title for m in qs}, {'Falcon', 'Frog', 'Toad', 'Duck'})

    def test_filter_i18n(self):
        Blog.objects.create(title='Cod')

        with override('nl'):
            # should fallback to english
            qs = Blog.objects.filter(title_i18n='Cod')
            self.assertEquals({m.title for m in qs}, {'Cod'})

            # should not fallback
            qs = Blog.objects.filter(title_nl='Cod')
            self.assertEquals({m.title for m in qs}, set())

    def test_filter_by_default_language(self):
        qs = Blog.objects.filter(title_en__contains='al')
        self.assertEquals({m.title for m in qs}, {'Falcon'})
        self.assertTrue('annotation' not in str(qs.query))

    def test_get(self):
        '''get() is just a special case of filter()'''
        b = Blog.objects.get(title_nl='Valk')

        self.assertEquals(b.title, 'Falcon')

        with self.assertRaisesMessage(Blog.DoesNotExist, 'Blog matching query does not exist.'):
            Blog.objects.get(title_fr='Boo')

    def test_filter_Q_object(self):
        b = Blog.objects.get(Q(title_nl__contains='al'))
        self.assertEquals(b.title, 'Falcon')

        qs = Blog.objects.filter(Q(title_nl__contains='al') | Q(title_en__contains='Fro'))
        self.assertEquals({m.title for m in qs}, {'Falcon', 'Frog'})

        b = Blog.objects.get(Q(title_nl__contains='al'), Q(title_en__contains='al'))
        self.assertEquals(b.title, 'Falcon')

        with override('nl'):
            b = Blog.objects.get(Q(title_i18n='Kikker'))
            self.assertEquals(b.title, 'Frog')

    def test_filter_F_expression(self):
        Blog.objects.create(title='foo', title_nl=20, title_fr=10)
        Blog.objects.create(title='bar', title_nl=20, title_fr=30)
        Blog.objects.create(title='baz', title_nl=20, title_fr=40)

        qs = Blog.objects.filter(title_nl__gt=F('title_fr'))
        self.assertEquals({m.title for m in qs}, {'foo'})

        qs = Blog.objects.filter(title_nl__lt=F('title_fr'))
        self.assertEquals({m.title for m in qs}, {'bar', 'baz'})

    def test_filter_relations(self):
        mass = Attribute.objects.create(slug='mass', name='Mean Mass')
        length = Attribute.objects.create(slug='length', name='Length', name_nl='Lengte')

        dog = Blog.objects.create(title='Australian Kelpie Dog')
        whale = Blog.objects.create(title='Blue Whale', title_nl='Blauwe vinvis')

        BlogAttr.objects.create(object=dog, attribute=mass, value=17)
        BlogAttr.objects.create(object=dog, attribute=length, value=.50)
        BlogAttr.objects.create(object=whale, attribute=mass, value=181000)
        BlogAttr.objects.create(object=whale, attribute=length, value=28)

        with override('nl'):
            Attribute.objects.filter(blogattr__object_id__in=Blog.objects.filter(title__contains='al'))

    def test_filter_subquery(self):
        '''
        When in a subquery, the table alias should be used rather than the real
        table name.
        '''
        c1 = Category.objects.create(name='Sofa', name_nl='Bank')
        c2 = Category.objects.create(name='modeltrans', name_nl='modeltrans')
        birds = Category.objects.create(name='Birds')

        Blog.objects.create(title='Chesterfield', category=c1)
        Blog.objects.create(title='Why migrate', category=c2)
        Blog.objects.create(title='Initial prototype', category=c2)
        Blog.objects.create(title='Dogfooding', category=c2)

        Blog.objects.create(title='Falcon', category=birds)

        qs = Blog.objects.filter(
            category__in=Category.objects.filter(name_nl__contains='an')
        )
        self.assertEquals(
            {m.title_i18n for m in qs},
            {'Chesterfield', 'Why migrate', 'Initial prototype', 'Dogfooding'}
        )

    def test_queryset_related_model(self):
        qs = Blog.objects.filter(category__name_nl='Vogels')
        self.assertEquals({m.title for m in qs}, {'Falcon', 'Duck'})

    def test_filter_spanning_relation(self):
        birds = Category.objects.get(name='Birds')
        bird_blogs = Blog.objects.filter(category=birds)

        self.assertEquals(
            {b.title for b in Blog.objects.filter(category__name_nl='Vogels')},
            {b.title for b in bird_blogs}
        )

    @skip('Not yet supported')
    def test_filter_spanning_relation_from_non_translatable(self):
        '''
        Not sure if we should support this, but it requires having
        `MultilingualManager` on non-translated models too.
        '''

        qs = Site.objects.filter(blog__title_nl__contains='al')
        print(qs.query)


class OrderByTest(TestCase):
    EN = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    NL = ['A', 'B', 'C', 'D', 'Z', 'Y', 'X']
    FR = ['1', '1', '1', '1', '2', '2', '2']

    def setUp(self):
        for i, en in enumerate(self.EN):
            Blog.objects.create(title=en, i18n={'title_nl': self.NL[i], 'title_fr': self.FR[i]})

    def test_regular_fields(self):
        qs = Blog.objects.all().order_by('-title')

        self.assertEquals(key(qs, 'title'), 'G,F,E,D,C,B,A'.split(','))

    def test_order_by_two_fields(self):
        '''Multiple translated fields should work too'''
        qs = Blog.objects.all().order_by('-title_fr', 'title_nl')

        self.assertEquals(key(qs, 'title_nl'), 'X,Y,Z,A,B,C,D'.split(','))

    def test_order_asc(self):
        qs = Blog.objects.all().order_by('title_nl')

        self.assertEquals(key(qs, 'title_nl'), sorted(self.NL))
        self.assertEquals(key(qs, 'title'), 'A,B,C,D,G,F,E'.split(','))

    def test_order_desc(self):
        qs = Blog.objects.all().order_by('-title_nl')
        self.assertEquals(key(qs, 'title_nl'), sorted(self.NL, reverse=True))

        qs = Blog.objects.all().order_by('-title')
        self.assertEquals(key(qs, 'title'), sorted(self.EN, reverse=True))

    def test_order_by_i18n(self):
        Blog.objects.create(title='H')
        with override('nl'):
            qs = Blog.objects.all().order_by('title_i18n')

            self.assertEquals(key(qs, 'title_i18n'), ['A', 'B', 'C', 'D', 'H', 'X', 'Y', 'Z'])

    def test_order_by_related_field(self):
        # TODO: implement
        pass


class FallbackOrderByTest(TestCase):

    @override_settings(
        MODELTRANS_AVAILABLE_LANGUAGES=('fr', 'fy', 'nl'),
        MODELTRANS_FALLBACK={
            'default': ('en', ),
            'fy': ('nl', 'en')
        },
        DEBUG=True
    )
    def test_order_by_fallback_chain(self):

        class TestObj(models.Model):
            title = models.CharField(max_length=100)
            i18n = TranslationField(fields=('title', ))

            class Meta:
                app_label = 'django-modeltrans_tests'

        translate_model(TestObj)

        with CreateTestModel(TestObj):
            TestObj.objects.bulk_create([
                TestObj(title='Falcon', title_nl='Valk'),
                TestObj(title='Frog', title_nl='Kikker', title_fr='Grenouilles', title_fy='Frosk'),
                TestObj(title='Fox', title_nl='Vos', title_fy='Foks'),
                TestObj(title='Gecko'),
                TestObj(title='Gerbil'),
                TestObj(title='Vulture', title_nl='Gier', title_fr='Vautour')
            ])

            # should use the 'default' fallback chain
            with override('nl'):
                qs = TestObj.objects.all().order_by('title_i18n')
                self.assertEquals(key(qs, 'title_i18n'), ['Gecko', 'Gerbil', 'Gier', 'Kikker', 'Valk', 'Vos'])

            # should use the 'fy' fallback chain
            with override('fy'):
                expected = ['Foks', 'Frosk', 'Gecko', 'Gerbil', 'Gier', 'Valk']
                qs = TestObj.objects.all().order_by('title_i18n')
                self.assertEquals(key(qs, 'title_i18n'), expected)

                expected.reverse()
                qs = TestObj.objects.all().order_by('-title_i18n')
                self.assertEquals(key(qs, 'title_i18n'), expected)

            # should use the 'default' fallback chain
            with override('fr'):
                qs = TestObj.objects.all().order_by('title_i18n')
                self.assertEquals(key(qs, 'title_i18n'), ['Falcon', 'Fox', 'Gecko', 'Gerbil', 'Grenouilles', 'Vautour'])


class FilteredOrderByTest(TestCase):
    def test_filtered_order_by(self):
        Blog.objects.bulk_create([
            Blog(title='Falcon', title_nl='Valk'),
            Blog(title='Frog', title_nl='Kikker'),
            Blog(title='Fox', title_nl='Vos'),
            Blog(title='Gecko'),
            Blog(title='Gerbil'),
            Blog(title='Vulture', title_nl='Gier')
        ])

        qs = Blog.objects.filter(title_en__contains='F').order_by('title_nl')
        self.assertEquals(key(qs, 'title_nl'), ['Kikker', 'Valk', 'Vos'])

        qs = Blog.objects.filter(title_en__contains='G').order_by('title_en')
        self.assertEquals(key(qs, 'title'), ['Gecko', 'Gerbil'])

        with override('nl'):
            qs = Blog.objects.filter(title_i18n__contains='G').order_by('title_i18n')
            self.assertEquals(key(qs, 'title_i18n'), ['Gecko', 'Gerbil', 'Gier'])

        with override('en'):
            qs = Blog.objects.filter(title_i18n__contains='G').order_by('-title_i18n')

            self.assertEquals(key(qs, 'title_i18n'), ['Gerbil', 'Gecko'])
            self.assertTrue('annotation' not in str(qs.query))


class ValuesTest(TestCase):
    def setUp(self):
        birds = Category.objects.create(name='Birds', name_nl='Vogels')
        amphibians = Category.objects.create(name='Amphibians', name_nl='Amfibiën')
        reptiles = Category.objects.create(name='Reptiles')

        Blog.objects.bulk_create([
            Blog(title='Falcon', title_nl='Valk', category=birds),
            Blog(title='Frog', title_nl='Kikker', category=amphibians),
            Blog(title='Gecko', category=reptiles),
        ])

    def assertEqualsList(self, qs, expected):
        try:
            self.assertEquals(list(qs), expected)
        except AssertionError:
            print('Queryset query: {}'.format(qs.query))

            raise

    def test_queryset_values_basic(self):
        self.assertEqualsList(
            Blog.objects.all().order_by('title_nl').values('title_nl'),
            [{'title_nl': None}, {'title_nl': 'Kikker'}, {'title_nl': 'Valk'}]
        )

    def test_queryset_values_default_language(self):
        self.assertEqualsList(
            Blog.objects.all().order_by('title_en').values('title_en'),
            [{'title_en': 'Falcon'}, {'title_en': 'Frog'}, {'title_en': 'Gecko'}]
        )

    def test_queryset_values_i18n(self):
        with override('nl'):
            self.assertEqualsList(
                Blog.objects.all().order_by('title_i18n').values('title_i18n'),
                [{'title_i18n': 'Gecko'}, {'title_i18n': 'Kikker'}, {'title_i18n': 'Valk'}]
            )

    def test_queryset_values_list(self):
        # doesn't make sense to add a much tests for values_list() specifically,
        # as the underlying function for value() is axactly the same.
        qs = Blog.objects.all().order_by('title_nl').values_list('title_nl')
        self.assertEquals(list(qs), [(None, ), ('Kikker', ), ('Valk', )])

    def test_queryset_values_list_default_language(self):
        self.assertEquals(
            list(Blog.objects.all().order_by('title_en').values_list('title_en')),
            list(Blog.objects.all().order_by('title').values_list('title')),
        )

    def test_queryset_related_model(self):
        self.assertEqualsList(
            Blog.objects.all().values_list('title_i18n', 'category__name_i18n'),
            [('Falcon', 'Birds'), ('Frog', 'Amphibians'), ('Gecko', 'Reptiles')]
        )

    @skip('Annotation of expressions in _values() not yet implemented.')
    def test_values_kwarg(self):
        from django.db.models.functions import Lower

        qs1 = Blog.objects.values(lower_name=Lower('category__name'))
        qs2 = Blog.objects.values(lower_name=Lower('category__name_en'))
        print(qs2.query)
        print(qs2)
        self.assertEquals(list(qs1), list(qs2))

    def test_values_spanning_relation(self):
        qs = Blog.objects.all().order_by('title_nl') \
            .values_list('title_nl', 'category__name_nl')
        self.assertEquals(
            list(qs),
            [(None, None), ('Kikker', 'Amfibiën'), ('Valk', 'Vogels')]
        )
