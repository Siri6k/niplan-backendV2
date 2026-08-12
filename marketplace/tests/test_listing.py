# marketplace/tests/test_listing.py

from django.db.models.deletion import ProtectedError
from django.test import TestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing


class ListingModelTests(TestCase):
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
        )

    def test_create_listing(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24 256GB",
            description="Samsung Galaxy S24 neuf, sous blister.",
            price=850.00,
            currency="USD",
            condition=Listing.Condition.NEW,
            stock=10,
            location="Kolwezi",
            is_negotiable=True,
        )

        self.assertEqual(listing.seller, self.seller)
        self.assertEqual(listing.store, self.store)
        self.assertEqual(listing.variant, self.variant)
        self.assertEqual(listing.price, 850)
        self.assertEqual(listing.stock, 10)
        self.assertEqual(listing.status, Listing.Status.DRAFT)
        self.assertTrue(listing.is_negotiable)

    def test_multiple_sellers_can_list_same_variant(self):
        listing_1 = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24 - Tech Store",
            price="850.00",
            currency="USD",
            stock=10,
        )

        user_2 = User.objects.create_user(
            email="seller2@niplan.com",
            password="TestPassword123!",
        )
        seller_2 = SellerProfile.objects.create(
            user=user_2,
            seller_type="INDIVIDUAL",
        )
        store_2 = Store.objects.create(
            seller=seller_2,
            name="Phone Store",
            slug="phone-store",
            city="Lubumbashi",
        )

        listing_2 = Listing.objects.create(
            seller=seller_2,
            store=store_2,
            variant=self.variant,
            title="Samsung S24 - Phone Store",
            price="820.00",
            currency="USD",
            stock=5,
        )

        self.assertEqual(self.variant.listings.count(), 2)
        self.assertNotEqual(listing_1.price, listing_2.price)

    def test_seller_with_listing_is_protected(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price="850.00",
            currency="USD",
            stock=10,
        )

        with self.assertRaises(ProtectedError):
            self.seller.delete()

    def test_store_with_listing_is_protected(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price="850.00",
            currency="USD",
            stock=10,
        )

        with self.assertRaises(ProtectedError):
            self.store.delete()

    def test_variant_with_listing_is_protected(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price="850.00",
            currency="USD",
            stock=10,
        )

        with self.assertRaises(ProtectedError):
            self.variant.delete()

    def test_listing_stock_positive(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price="850.00",
            stock=0,
        )
        self.assertEqual(listing.stock, 0)

    def test_listing_status_transitions(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price="850.00",
            status=Listing.Status.DRAFT,
        )

        listing.status = Listing.Status.PUBLISHED
        listing.save()
        listing.refresh_from_db()

        self.assertEqual(listing.status, Listing.Status.PUBLISHED)

    def test_listing_is_available(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price="850.00",
            status=Listing.Status.PUBLISHED,
            stock=5,
        )
        self.assertTrue(listing.is_available)

        listing.stock = 0
        listing.save()
        self.assertFalse(listing.is_available)

        listing.stock = 5
        listing.status = Listing.Status.PAUSED
        listing.save()
        self.assertFalse(listing.is_available)
