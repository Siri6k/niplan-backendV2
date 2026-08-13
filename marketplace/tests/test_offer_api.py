from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User, SellerProfile, Store
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing, Offer


class OfferAPITests(APITestCase):

    def setUp(self):
        self.buyer = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )

        self.seller_user = User.objects.create_user(
            email="seller@niplan.com",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            email="other@niplan.com",
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

    def test_authenticated_buyer_can_create_offer(self):
        self.client.force_authenticate(user=self.buyer)

        url = reverse(
            "marketplace:listing-offers",
            kwargs={"pk": self.listing.pk},
        )

        response = self.client.post(
            url,
            data={
                "unit_amount": "800.00",
                "quantity": 2,
                "message": "Je peux prendre aujourd'hui.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["unit_amount"], "800.00")
        self.assertEqual(response.data["quantity"], 2)
        self.assertEqual(response.data["total_amount"], 1600.00)
        self.assertTrue(
            Offer.objects.filter(
                buyer=self.buyer,
                listing=self.listing,
            ).exists()
        )

    def test_anonymous_cannot_create_offer(self):
        url = reverse(
            "marketplace:listing-offers",
            kwargs={"pk": self.listing.pk},
        )

        response = self.client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_seller_can_accept_offer(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800.00,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        self.client.force_authenticate(user=self.seller_user)

        url = reverse(
            "marketplace:offer-actions",
            kwargs={"pk": offer.pk},
        )

        response = self.client.post(
            url,
            data={"action": "accept"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Offer.Status.ACCEPTED)

    def test_buyer_can_cancel_offer(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800.00,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        self.client.force_authenticate(user=self.buyer)

        url = reverse(
            "marketplace:offer-actions",
            kwargs={"pk": offer.pk},
        )

        response = self.client.post(
            url,
            data={"action": "cancel"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Offer.Status.CANCELLED)

    def test_counter_offer(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=750.00,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        self.client.force_authenticate(user=self.seller_user)

        url = reverse(
            "marketplace:offer-actions",
            kwargs={"pk": offer.pk},
        )

        response = self.client.post(
            url,
            data={
                "action": "counter",
                "unit_amount": "820.00",
                "message": "Je peux faire 820.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Offer.Status.PENDING)
        self.assertEqual(response.data["unit_amount"], "820.00")

        offer.refresh_from_db()
        self.assertEqual(offer.status, Offer.Status.COUNTERED)

    def test_cannot_counter_as_non_participant(self):
        offer = Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=750.00,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        self.client.force_authenticate(user=self.other_user)

        url = reverse(
            "marketplace:offer-actions",
            kwargs={"pk": offer.pk},
        )

        response = self.client.post(
            url,
            data={
                "action": "counter",
                "unit_amount": "820.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_my_offers(self):
        Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800.00,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        self.client.force_authenticate(user=self.buyer)

        url = reverse("marketplace:my-offers")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["listing_title"], "Samsung Galaxy S24")

    def test_seller_offers(self):
        Offer.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            unit_amount=800.00,
            currency="USD",
            quantity=1,
            status=Offer.Status.PENDING,
        )

        self.client.force_authenticate(user=self.seller_user)

        url = reverse("marketplace:seller-offers")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
