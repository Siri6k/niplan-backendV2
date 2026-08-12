# marketplace/tests/test_listing_service.py

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from marketplace.services.listing_service import ListingService


class ListingServiceTests(TestCase):
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
            status=Product.Status.ACTIVE,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="SAM-S24-BLK-256",
            is_active=True,
        )

    def test_create_listing(self):
        listing = ListingService.create_listing(
            user=self.user,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
        )

        self.assertEqual(listing.seller, self.seller)
        self.assertEqual(listing.store, self.store)
        self.assertEqual(listing.variant, self.variant)
        self.assertEqual(listing.price, Decimal("850.00"))
        self.assertEqual(listing.status, Listing.Status.DRAFT)

    def test_cannot_create_listing_in_someone_else_store(self):
        user_2 = User.objects.create_user(
            email="seller2@niplan.com",
            password="TestPassword123!",
        )
        SellerProfile.objects.create(
            user=user_2,
            seller_type="INDIVIDUAL",
        )

        with self.assertRaises(ValidationError):
            ListingService.create_listing(
                user=user_2,
                store=self.store,
                variant=self.variant,
                title="Unauthorized listing",
                price=Decimal("500.00"),
                stock=5,
            )

    def test_cannot_create_listing_for_inactive_variant(self):
        self.variant.is_active = False
        self.variant.save()

        with self.assertRaises(ValidationError):
            ListingService.create_listing(
                user=self.user,
                store=self.store,
                variant=self.variant,
                title="Inactive variant",
                price=Decimal("500.00"),
                stock=5,
            )

    def test_cannot_create_listing_for_inactive_product(self):
        self.product.status = Product.Status.ARCHIVED
        self.product.save()

        with self.assertRaises(ValidationError):
            ListingService.create_listing(
                user=self.user,
                store=self.store,
                variant=self.variant,
                title="Inactive product",
                price=Decimal("500.00"),
                stock=5,
            )

    def test_price_must_be_positive(self):
        with self.assertRaises(ValidationError):
            ListingService.create_listing(
                user=self.user,
                store=self.store,
                variant=self.variant,
                title="Invalid price",
                price=Decimal("0.00"),
                stock=5,
            )

    def test_negative_price_is_rejected(self):
        with self.assertRaises(ValidationError):
            ListingService.create_listing(
                user=self.user,
                store=self.store,
                variant=self.variant,
                title="Invalid price",
                price=Decimal("-10.00"),
                stock=5,
            )

    def test_publish_listing(self):
        listing = ListingService.create_listing(
            user=self.user,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            stock=10,
        )

        ListingService.publish_listing(listing=listing, user=self.user)
        listing.refresh_from_db()

        self.assertEqual(listing.status, Listing.Status.PUBLISHED)
        self.assertIsNotNone(listing.published_at)

    def test_cannot_publish_without_stock(self):
        listing = ListingService.create_listing(
            user=self.user,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            stock=0,
        )

        with self.assertRaises(ValidationError):
            ListingService.publish_listing(listing=listing, user=self.user)

    def test_other_seller_cannot_publish_listing(self):
        listing = ListingService.create_listing(
            user=self.user,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            stock=10,
        )

        user_2 = User.objects.create_user(
            email="seller2@niplan.com",
            password="TestPassword123!",
        )
        SellerProfile.objects.create(
            user=user_2,
            seller_type="INDIVIDUAL",
        )

        with self.assertRaises(ValidationError):
            ListingService.publish_listing(listing=listing, user=user_2)

    def test_pause_listing(self):
        listing = ListingService.create_listing(
            user=self.user,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            stock=10,
        )
        ListingService.publish_listing(listing=listing, user=self.user)
        ListingService.pause_listing(listing=listing, user=self.user)

        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.PAUSED)

    def test_archive_listing(self):
        listing = ListingService.create_listing(
            user=self.user,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            stock=10,
        )
        ListingService.archive_listing(listing=listing, user=self.user)

        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.ARCHIVED)

    def test_cannot_pause_non_published_listing(self):
        listing = ListingService.create_listing(
            user=self.user,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            stock=10,
        )

        with self.assertRaises(ValidationError):
            ListingService.pause_listing(listing=listing, user=self.user)

    def test_cannot_publish_archived_listing(self):
        listing = ListingService.create_listing(
            user=self.user,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            stock=10,
        )
        ListingService.archive_listing(listing=listing, user=self.user)

        with self.assertRaises(ValidationError):
            ListingService.publish_listing(listing=listing, user=self.user)
