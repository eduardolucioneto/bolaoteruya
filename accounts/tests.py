from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import PoolConfiguration


class AccountsTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(username="ana", email="ana@example.com", password="Senha123456")

    def test_login_works(self):
        response = self.client.post(reverse("accounts:login"), {"username": "ana", "password": "Senha123456"})
        self.assertEqual(response.status_code, 302)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

    def test_signup_obeys_configuration(self):
        config = PoolConfiguration.get_solo()
        config.allow_self_signup = False
        config.save()
        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 302)

    def test_admin_requires_staff(self):
        self.client.login(username="ana", password="Senha123456")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
