# coding: utf-8
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views import static

from app.views import BlogListView, BlogUpdateView, BlogView, FilteredBlogListView, fixtures

admin.autodiscover()

urlpatterns = [
    url(r'^blogs/', BlogListView.as_view(), name='blogs'),
    url(r'^blogs-filter/', FilteredBlogListView.as_view(), name='blogs'),
    url(r'^blog/(?P<pk>\d+)/edit/', BlogUpdateView.as_view(), name='blog-edit'),
    url(r'^blog/(?P<pk>\d+)/', BlogView.as_view(), name='blog'),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),

    url(r'^media/(?P<path>.*)$', static.serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
    url(r'fixtures/', fixtures, name='fixtures'),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'$', BlogListView.as_view(), name='index'),
]
