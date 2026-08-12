from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import SellerProfile, Store
from accounts.permissions import IsSeller, IsStoreOwner

User = get_user_model()


class PermissionsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@niplan.com", password="StrongPassword123!"
        )
        self.seller_user = User.objects.create_user(
            email="seller@niplan.com", password="StrongPassword123!"
        )
        self.seller = SellerProfile.objects.create(
            user=self.seller_user, seller_type="INDIVIDUAL"
        )
        self.store = Store.objects.create(
            seller=self.seller, name="Test Store", slug="test-store"
        )

    def _mock_request(self, user):
        class MockRequest:
            def __init__(self, user):
                self.user = user

        return MockRequest(user)

    def test_is_seller_with_seller(self):
        perm = IsSeller()
        request = self._mock_request(self.seller_user)
        self.assertTrue(perm.has_permission(request, None))

    def test_is_seller_without_seller(self):
        perm = IsSeller()
        request = self._mock_request(self.user)
        self.assertFalse(perm.has_permission(request, None))

    def test_is_store_owner_true(self):
        perm = IsStoreOwner()
        request = self._mock_request(self.seller_user)
        self.assertTrue(perm.has_object_permission(request, None, self.store))

    def test_is_store_owner_false(self):
        other_user = User.objects.create_user(
            email="other@niplan.com", password="StrongPassword123!"
        )
        perm = IsStoreOwner()
        request = self._mock_request(other_user)
        self.assertFalse(perm.has_object_permission(request, None, self.store))
