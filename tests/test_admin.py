from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from .app.models import Category, Site
from .utils import load_wiki

User = get_user_model()

TEST_USERNAME = "admin"
TEST_PASSWORD = "battery-horse-staple"


class AdminTest(TestCase):
    @classmethod
    def setUpTestData(self):
        User.objects.create_superuser(
            username=TEST_USERNAME, email="test@example.com", password=TEST_PASSWORD
        )
        load_wiki()

    def setUp(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        self.site = Site.objects.create(name="Default site")
        self.wikipedia = Category.objects.get(name="Wikipedia")

    def test_limited_admin(self):
        url = reverse("admin:app_category_changelist")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.wikipedia.name)

        with override("nl"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, self.wikipedia.name)

        with override("de"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, self.wikipedia.name)

    def test_change_view(self):
        url = reverse("admin:app_category_change", args=(self.wikipedia.pk,))

        with override("nl"):
            response = self.client.get(url)
            self.assertNotContains(response, "name_de")
            self.assertContains(response, "name_nl")

        with override("de"):
            response = self.client.get(url)
            self.assertNotContains(response, "name_nl")
            self.assertContains(response, "name_de")

    def test_non_translated_admin(self):
        url = reverse("admin:app_site_change", args=(self.site.pk,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_search(self):
        def url(q):
            return "{}?q={}".format(reverse("admin:app_blog_changelist"), q)

        with override("nl"):
            response = self.client.get(url("kker"))
            self.assertContains(response, "Kikkers")

        with override("en"):
            response = self.client.get(url("kker"))
            self.assertNotContains(response, "Kikkers")

            response = self.client.get(url("frog"))
            self.assertContains(response, "Frog")
