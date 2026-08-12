from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Profile

User = get_user_model()


class ProfileTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:profile-me")
        self.user = User.objects.create_user(
            email="test@niplan.com", password="StrongPassword123!"
        )
        refresh = RefreshToken.for_user(self.user)
        self.auth_header = f"Bearer {refresh.access_token}"

    def test_profile_created_with_user(self):
        """Le signal doit avoir créé le Profile automatiquement."""
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_get_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@niplan.com")

    def test_patch_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        payload = {
            "bio": "Vendeur à Kolwezi",
            "city": "Kolwezi",
            "country": "CD",
            "preferred_currency": "USD",
        }
        response = self.client.patch(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city"], "Kolwezi")
        self.assertEqual(response.data["country"], "CD")

    def test_profile_requires_auth(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
