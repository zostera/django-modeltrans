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


class FilterTest(TestCase):
    data = (
        ('Falcon', 'Valk'),
        ('Frog', 'Kikker'),
        ('Toad', 'Pad'),
        ('Duck', 'Eend'),
        ('Dolphin', 'Dolfijn')
    )

    def setUp(self):
        for title, title_nl in self.data:
            Blog.objects.create(title=title, i18n={'title_nl': title_nl})

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

        self.assertEquals(len(list(qs)), 4)

    @skip('Not yet implemented')
    def test_filter_spanning_relation(self):
        birds = Category.objects.create(name='Birds', name_nl='Vogels')
        bird_blogs = Blog.objects.filter(title__in=('Duck', 'Falcon'))
        bird_blogs.update(category=birds)

        self.assertEquals(
            {b.name for b in Blog.objects.filter(category__name_nl='Vogels')},
            {b.name for b in bird_blogs}
        )

    @skip('Not yet implemented')
    def test_filter_spanning_relation_from_non_translatable(self):
        '''
        Not sure if we should support this, but it requires having
        `MultilingualManager` on non-translated models too.
        '''

        Site.objects.filter(blog__title_nl__contains='al')


class OrderByTest(TestCase):
    EN = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    NL = ['A', 'B', 'C', 'D', 'Z', 'Y', 'X']
    FR = ['1', '1', '1', '1', '2', '2', '2']

    def setUp(self):
        for i, en in enumerate(self.EN):
            Blog.objects.create(title=en, i18n={'title_nl': self.NL[i], 'title_fr': self.FR[i]})

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

    def test_queryset_values_basic(self):
        self.assertEquals(
            list(Blog.objects.all().order_by('title_nl').values('title_nl')),
            [{'title_nl': None}, {'title_nl': 'Kikker'}, {'title_nl': 'Valk'}]
        )

    def test_queryset_values_default_language(self):
        self.assertEquals(
            list(Blog.objects.all().order_by('title_en').values('title_en')),
            [{'title_en': 'Falcon'}, {'title_en': 'Frog'}, {'title_en': 'Gecko'}]
        )

    def test_queryset_values_i18n(self):
        with override('nl'):
            self.assertEquals(
                list(Blog.objects.all().order_by('title_i18n').values('title_i18n')),
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

    def test_values_spanning_relation(self):
        qs = Blog.objects.all().order_by('title_nl') \
            .values_list('title_nl', 'category__name_nl')
        print(qs.query)
        self.assertEquals(
            list(qs),
            [(None, None), ('Kikker', 'Amfibiën'), ('Valk', 'Vogels')]
        )
