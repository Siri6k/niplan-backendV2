from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User, SellerProfile, Store
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Favorite, Listing


class FavoriteAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )

        self.seller_user = User.objects.create_user(
            email="seller@niplan.com",
            password="TestPassword123!",
        )

        self.seller = SellerProfile.objects.create(
            user=self.seller_user,
            seller_type="INDIVIDUAL",
        )

        self.store = Store.objects.create(
            seller=self.seller,
            name="Tech Store",
            slug="tech-store",
            city="Kolwezi",
        )

        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Samsung Galaxy S24",
            brand="Samsung",
            model="Galaxy S24",
            slug="samsung-galaxy-s24",
        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="SAM-S24-BLK-256",
            # name="Black 256GB",  # SUPPRIMÉ — champ inexistant
        )

        self.listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price="850.00",
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )

    def test_authenticated_user_can_favorite(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            "marketplace:listing-favorite",
            kwargs={"pk": self.listing.pk},
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Favorite.objects.filter(
                user=self.user,
                listing=self.listing,
            ).exists()
        )

    def test_anonymous_user_cannot_favorite(self):
        url = reverse(
            "marketplace:listing-favorite",
            kwargs={"pk": self.listing.pk},
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 401)

    def test_user_can_get_favorites(self):
        Favorite.objects.create(
            user=self.user,
            listing=self.listing,
        )

        self.client.force_authenticate(user=self.user)

        url = reverse("marketplace:favorite-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
