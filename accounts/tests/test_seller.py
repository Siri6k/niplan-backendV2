from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import SellerProfile

User = get_user_model()


class SellerTests(APITestCase):
    def setUp(self):
        self.become_url = reverse("accounts:become-seller")
        self.me_url = reverse("accounts:seller-me")
        self.user = User.objects.create_user(
            email="seller@niplan.com", password="StrongPassword123!"
        )
        refresh = RefreshToken.for_user(self.user)
        self.auth_header = f"Bearer {refresh.access_token}"

    def test_become_seller(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        payload = {"seller_type": "INDIVIDUAL"}
        response = self.client.post(self.become_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SellerProfile.objects.count(), 1)
        self.assertEqual(response.data["seller_type"], "INDIVIDUAL")
        self.assertEqual(response.data["verification_status"], "PENDING")

    def test_become_seller_twice_fails(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        SellerProfile.objects.create(user=self.user, seller_type="INDIVIDUAL")

        payload = {"seller_type": "BUSINESS"}
        response = self.client.post(self.become_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_seller_me(self):
        SellerProfile.objects.create(user=self.user, seller_type="INDIVIDUAL")
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)

        response = self.client.get(self.me_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["seller_type"], "INDIVIDUAL")

    def test_seller_me_requires_seller(self):
        """Un user sans seller_profile doit être rejeté."""
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        response = self.client.get(self.me_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
