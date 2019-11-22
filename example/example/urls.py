from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views import static

from app.views import BlogListView, BlogUpdateView, BlogView, FilteredBlogListView, fixtures

admin.autodiscover()

urlpatterns = [
    path("blogs/", BlogListView.as_view(), name="blogs"),
    path("blogs-filter/", FilteredBlogListView.as_view(), name="blogs"),
    path("blog/<int:pk>/edit/", BlogUpdateView.as_view(), name="blog-edit"),
    path("blog/<int:pk>/", BlogView.as_view(), name="blog_detail"),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("media/<str:path>/", static.serve, {"document_root": settings.MEDIA_ROOT}),
    path("fixtures/", fixtures, name="fixtures"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", BlogListView.as_view(), name="index"),
]
