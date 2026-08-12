from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from accounts.models import User, SellerProfile, Store
from catalog.models import Category, Product, ProductVariant

from marketplace.models import Favorite, Listing
from marketplace.services.favorite_service import FavoriteService


class FavoriteTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="seller@niplan.com",
            password="TestPassword123!",
        )

        self.seller = SellerProfile.objects.create(
            user=self.user,
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

    def test_add_favorite(self):
        favorite = Favorite.objects.create(
            user=self.user,
            listing=self.listing,
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.listing, self.listing)

    def test_same_listing_cannot_be_favorited_twice(self):
        Favorite.objects.create(
            user=self.user,
            listing=self.listing,
        )

        with self.assertRaises(IntegrityError):
            Favorite.objects.create(
                user=self.user,
                listing=self.listing,
            )

    def test_service_add_favorite(self):
        favorite = FavoriteService.add_favorite(
            user=self.user,
            listing=self.listing,
        )
        self.assertEqual(favorite.listing, self.listing)
        self.assertTrue(
            FavoriteService.is_favorite(
                user=self.user,
                listing=self.listing,
            )
        )

    def test_remove_favorite(self):
        Favorite.objects.create(
            user=self.user,
            listing=self.listing,
        )

        FavoriteService.remove_favorite(
            user=self.user,
            listing=self.listing,
        )

        self.assertFalse(
            Favorite.objects.filter(
                user=self.user,
                listing=self.listing,
            ).exists()
        )

    def test_cannot_favorite_unpublished_listing(self):
        self.listing.status = Listing.Status.DRAFT
        self.listing.save()

        with self.assertRaises(ValidationError):
            FavoriteService.add_favorite(
                user=self.user,
                listing=self.listing,
            )
