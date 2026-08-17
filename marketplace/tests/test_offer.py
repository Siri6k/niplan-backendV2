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

        self.random_user = User.objects.create_user(
            email="random@niplan.com",
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
            )

    def test_cannot_offer_on_unpublished_listing(self):
        self.listing.status = Listing.Status.DRAFT
        self.listing.save()

        with self.assertRaises(ValidationError):
            OfferService.create_offer(
                buyer=self.buyer,
                listing=self.listing,
                unit_amount=800.00,
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
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        accepted = OfferService.accept_offer(
            offer=offer,
            user=self.seller_user,
        )

        self.assertEqual(accepted.status, Offer.Status.ACCEPTED)
        self.assertIsNotNone(accepted.responded_at)

    def test_random_user_cannot_accept_offer(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        with self.assertRaises(ValidationError):
            OfferService.accept_offer(
                offer=offer,
                user=self.random_user,
            )

    def test_seller_can_reject_offer(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        rejected = OfferService.reject_offer(
            offer=offer,
            user=self.seller_user,
        )

        self.assertEqual(rejected.status, Offer.Status.REJECTED)

    def test_buyer_can_cancel_offer(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        OfferService.cancel_offer(
            offer=offer,
            user=self.buyer,
        )

        offer.refresh_from_db()
        self.assertEqual(offer.status, Offer.Status.CANCELLED)

    def test_seller_cannot_cancel_offer(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        with self.assertRaises(ValidationError):
            OfferService.cancel_offer(
                offer=offer,
                user=self.seller_user,
            )

    def test_accepted_offer_cannot_be_rejected(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800,
            currency="USD",
            quantity=1,
            status=Offer.Status.ACCEPTED,
        )

        with self.assertRaises(ValidationError):
            OfferService.reject_offer(
                offer=offer,
                user=self.seller_user,
            )

    def test_seller_can_counter_offer(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=750,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        counter = OfferService.counter_offer(
            offer=offer,
            user=self.seller_user,
            unit_amount=820,
            message="820 USD maximum.",
        )

        offer.refresh_from_db()

        self.assertEqual(offer.status, Offer.Status.COUNTERED)
        self.assertEqual(counter.status, Offer.Status.PENDING)
        self.assertEqual(counter.parent_offer, offer)
        self.assertEqual(counter.unit_amount, 820)

    def test_offer_negotiation_chain(self):
        first = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=750,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        second = OfferService.counter_offer(
            offer=first,
            user=self.seller_user,
            unit_amount=820,
        )

        third = OfferService.counter_offer(
            offer=second,
            user=self.buyer,
            unit_amount=800,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertEqual(first.status, Offer.Status.COUNTERED)
        self.assertEqual(second.status, Offer.Status.COUNTERED)
        self.assertEqual(third.status, Offer.Status.PENDING)
        self.assertEqual(third.parent_offer, second)

    def test_str_representation(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800.00,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )
        expected = f"{self.buyer} → {self.listing} : 800.0 USD"
        self.assertEqual(str(offer), expected)
