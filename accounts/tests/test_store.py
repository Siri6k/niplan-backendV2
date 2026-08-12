from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import SellerProfile, Store

User = get_user_model()


class StoreTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="store@niplan.com", password="StrongPassword123!"
        )
        self.seller = SellerProfile.objects.create(
            user=self.user, seller_type="BUSINESS"
        )
        refresh = RefreshToken.for_user(self.user)
        self.auth_header = f"Bearer {refresh.access_token}"
        self.url = reverse("accounts:store")  # plus de "store-list"

    def test_create_store(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        payload = {
            "name": "ABC Electronics",
            "description": "Téléphones et accessoires",
            "city": "Kolwezi",
            "phone": "+243999999999",
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(response.data["name"], "ABC Electronics")
        self.assertTrue(response.data["slug"])

    def test_create_store_twice_fails(self):
        Store.objects.create(
            seller=self.seller, name="Existing Store", slug="existing-store"
        )
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)

        payload = {"name": "Another Store", "city": "Lubumbashi"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_store(self):
        Store.objects.create(
            seller=self.seller,
            name="ABC Electronics",
            slug="abc-electronics",
            city="Kolwezi",
        )
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "ABC Electronics")

    def test_patch_store(self):
        Store.objects.create(
            seller=self.seller,
            name="Old Name",
            slug="old-name",
            city="Kolwezi",
        )
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)

        # Plus besoin de pk dans l'URL
        response = self.client.patch(
            self.url, {"name": "New Name", "city": "Lubumbashi"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "New Name")
        self.assertEqual(response.data["city"], "Lubumbashi")

    def test_store_requires_seller(self):
        plain_user = User.objects.create_user(
            email="plain@niplan.com", password="StrongPassword123!"
        )
        refresh = RefreshToken.for_user(plain_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
