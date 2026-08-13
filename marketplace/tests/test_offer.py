from django.test import TestCase
from django.core.exceptions import ValidationError

from accounts.models import User, SellerProfile, Store
from catalog.models import Category, Product, ProductVariant

from marketplace.models import Listing, Offer
from marketplace.services.offer_service import OfferService


class OfferTests(TestCase):

    def setUp(self):
        self.buyer = User.objects.create_user(
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

    def test_create_offer_service(self):
        offer = OfferService.create_offer(
            buyer=self.buyer,
            listing=self.listing,
            unit_amount=800.00,
            quantity=2,
            message="Je peux prendre aujourd'hui.",
        )

        self.assertEqual(offer.unit_amount, 800.00)
        self.assertEqual(offer.quantity, 2)
        self.assertEqual(offer.total_amount, 1600.00)
        self.assertEqual(offer.currency, "USD")
        self.assertEqual(offer.status, Offer.Status.PENDING)
        self.assertEqual(offer.buyer, self.buyer)

    def test_buyer_cannot_be_seller(self):
        with self.assertRaises(ValidationError):
            OfferService.create_offer(
                buyer=self.seller_user,
                listing=self.listing,
                unit_amount=800.00,
                quantity=1,
            )

    def test_cannot_offer_on_unpublished_listing(self):
        self.listing.status = Listing.Status.DRAFT
        self.listing.save()

        with self.assertRaises(ValidationError):
            OfferService.create_offer(
                buyer=self.buyer,
                listing=self.listing,
                unit_amount=800.00,
                quantity=1,
            )

    def test_quantity_cannot_exceed_stock(self):
        with self.assertRaises(ValidationError):
            OfferService.create_offer(
                buyer=self.buyer,
                listing=self.listing,
                unit_amount=800.00,
                quantity=20,
            )

    def test_seller_can_accept_offer(self):
        offer = OfferService.create_offer(
            buyer=self.buyer,
            listing=self.listing,
            unit_amount=800.00,
            quantity=1,
        )

        accepted = OfferService.accept_offer(
            offer=offer,
            user=self.seller_user,
        )

        self.assertEqual(accepted.status, Offer.Status.ACCEPTED)
        self.assertIsNotNone(accepted.responded_at)

    def test_seller_can_reject_offer(self):
        offer = OfferService.create_offer(
            buyer=self.buyer,
            listing=self.listing,
            unit_amount=800.00,
            quantity=1,
        )

        rejected = OfferService.reject_offer(
            offer=offer,
            user=self.seller_user,
        )

        self.assertEqual(rejected.status, Offer.Status.REJECTED)

    def test_buyer_can_cancel_offer(self):
        offer = OfferService.create_offer(
            buyer=self.buyer,
            listing=self.listing,
            unit_amount=800.00,
            quantity=1,
        )

        cancelled = OfferService.cancel_offer(
            offer=offer,
            user=self.buyer,
        )

        self.assertEqual(cancelled.status, Offer.Status.CANCELLED)

    def test_counter_offer(self):
        offer = OfferService.create_offer(
            buyer=self.buyer,
            listing=self.listing,
            unit_amount=750.00,
            quantity=1,
        )

        counter = OfferService.counter_offer(
            offer=offer,
            user=self.seller_user,
            unit_amount=820.00,
            message="Je peux descendre à 820.",
        )

        self.assertEqual(counter.status, Offer.Status.PENDING)
        self.assertEqual(counter.parent_offer, offer)
        self.assertEqual(counter.unit_amount, 820.00)

        offer.refresh_from_db()
        self.assertEqual(offer.status, Offer.Status.COUNTERED)

    def test_cannot_accept_non_pending_offer(self):
        offer = OfferService.create_offer(
            buyer=self.buyer,
            listing=self.listing,
            unit_amount=800.00,
        )
        OfferService.reject_offer(offer=offer, user=self.seller_user)

        with self.assertRaises(ValidationError):
            OfferService.accept_offer(offer=offer, user=self.seller_user)

    def test_str_representation(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800.15,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )
        expected = f"{self.buyer} → {self.listing} : 800.15 USD"
        self.assertEqual(str(offer), expected)
