from django.urls import reverse
from rest_framework.test import APITestCase

from analytics.models import AnalyticsEvent
from base_api.models import User
from listing.models import Listing


class ListingAPITest(APITestCase):
    def setUp(self):
        self.vendor_user = User.objects.create_user(
            phone_whatsapp="243810000001",
            password="password123",
            is_active=True,
            is_phone_verified=True,
        )
        self.other_user = User.objects.create_user(
            phone_whatsapp="243810000002",
            password="password123",
            is_active=True,
            is_phone_verified=True,
        )

        self.vendor_business = self.vendor_user.business
        self.vendor_business.name = "Niplan Mode"
        self.vendor_business.business_type = "SHOP"
        self.vendor_business.save()

        self.other_business = self.other_user.business
        self.other_business.name = "Tech Congo"
        self.other_business.business_type = "SHOP"
        self.other_business.save()

        self.mode_listing = Listing.objects.create(
            business=self.vendor_business,
            title="Chemise premium",
            description="Chemise coton pour bureau",
            price=25,
            currency="USD",
            category="Mode",
            ville="Kinshasa",
            commune="Gombe",
            quartier="Centre",
        )
        self.inactive_listing = Listing.objects.create(
            business=self.vendor_business,
            title="Sac archive",
            description="Ancienne annonce vendeur",
            price=15,
            currency="USD",
            category="Mode",
            ville="Kinshasa",
            commune="Limete",
            is_active=False,
        )
        Listing.objects.filter(id=self.inactive_listing.id).update(is_active=False)
        self.inactive_listing.refresh_from_db()
        self.phone_listing = Listing.objects.create(
            business=self.other_business,
            title="iPhone 14",
            description="Smartphone neuf garanti",
            price=700,
            currency="USD",
            category="Electronique",
            ville="Lubumbashi",
            commune="Golf",
            quartier="Ville",
            is_promoted=True,
        )
        self.barter_listing = Listing.objects.create(
            business=self.other_business,
            title="Canape troc",
            description="Canape contre table",
            price=100,
            currency="USD",
            category="Maison",
            ville="Kinshasa",
            commune="Ngaliema",
            is_for_barter=True,
            barter_target="Table",
        )

        for _ in range(3):
            AnalyticsEvent.objects.create(
                event_type="listing_view",
                source="test",
                business=self.other_business,
                listing=self.phone_listing,
            )
        AnalyticsEvent.objects.create(
            event_type="whatsapp_click",
            source="test",
            business=self.other_business,
            listing=self.phone_listing,
        )
        AnalyticsEvent.objects.create(
            event_type="listing_view",
            source="test",
            business=self.vendor_business,
            listing=self.mode_listing,
        )

    def test_public_listings_can_filter_by_category_and_city(self):
        response = self.client.get(
            reverse("public-listings"),
            {"category": "Mode", "ville": "Kinshasa"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.mode_listing.slug)

    def test_public_listings_can_search_title_description_and_business(self):
        response = self.client.get(reverse("public-listings"), {"search": "iphone"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.phone_listing.slug)

    def test_public_listings_can_order_by_price_desc(self):
        response = self.client.get(reverse("public-listings"), {"ordering": "price_desc"})

        self.assertEqual(response.status_code, 200)
        prices = [float(item["price"]) for item in response.data["results"]]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_public_listings_can_paginate_with_page_size(self):
        response = self.client.get(reverse("public-listings"), {"page_size": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])

    def test_public_listings_can_filter_barter_and_price_range(self):
        response = self.client.get(
            reverse("public-listings"),
            {"is_for_barter": "true", "min_price": "50", "max_price": "150"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.barter_listing.slug)

    def test_public_listings_can_order_by_popular(self):
        response = self.client.get(reverse("public-listings"), {"ordering": "popular"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["slug"], self.phone_listing.slug)

    def test_vendor_listings_are_scoped_to_authenticated_business(self):
        self.client.force_authenticate(self.vendor_user)

        response = self.client.get("/api/v2/listings/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        returned_slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(returned_slugs, {self.mode_listing.slug, self.inactive_listing.slug})

    def test_vendor_listings_can_filter_inactive(self):
        self.client.force_authenticate(self.vendor_user)

        response = self.client.get("/api/v2/listings/", {"is_active": "false"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.inactive_listing.slug)

    def test_vendor_listings_can_search_and_order_by_views(self):
        self.client.force_authenticate(self.vendor_user)

        response = self.client.get(
            "/api/v2/listings/",
            {"search": "chemise", "ordering": "views"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.mode_listing.slug)
