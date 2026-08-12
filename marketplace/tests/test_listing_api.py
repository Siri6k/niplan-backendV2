# marketplace/tests/test_listing_api.py

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing


class ListingAPITests(APITestCase):
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

        self.url = reverse("marketplace:listing-list")

    def test_public_can_list_published_listings(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_public_cannot_see_draft(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Draft S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_authenticated_seller_can_create_listing(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "store": str(self.store.pk),
            "variant": str(self.variant.pk),
            "title": "Samsung Galaxy S24",
            "description": "Neuf sous blister",
            "price": "850.00",
            "currency": "USD",
            "condition": "NEW",
            "stock": 10,
            "location": "Kolwezi",
            "is_negotiable": True,
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Listing.objects.count(), 1)
        self.assertEqual(response.data["status"], "DRAFT")

    def test_anonymous_cannot_create_listing(self):
        payload = {
            "store": str(self.store.pk),
            "variant": str(self.variant.pk),
            "title": "Samsung Galaxy S24",
            "price": "850.00",
            "currency": "USD",
            "stock": 10,
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_seller_can_publish_listing(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-actions", kwargs={"pk": listing.pk})
        response = self.client.post(url, {"action": "publish"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.PUBLISHED)

    def test_other_seller_cannot_publish(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
        )
        user_2 = User.objects.create_user(
            email="seller2@niplan.com",
            password="TestPassword123!",
        )
        SellerProfile.objects.create(user=user_2, seller_type="INDIVIDUAL")
        self.client.force_authenticate(user=user_2)
        url = reverse("marketplace:listing-actions", kwargs={"pk": listing.pk})
        response = self.client.post(url, {"action": "publish"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_can_see_published_detail(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Samsung S24")

    def test_public_cannot_see_draft_detail(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Draft S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_see_own_draft_detail(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="My Draft",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "My Draft")

    def test_seller_can_delete_draft(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="To Delete",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Listing.objects.count(), 0)

    def test_seller_cannot_delete_published(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Published",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_seller_cannot_delete(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Protected",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        user_2 = User.objects.create_user(
            email="seller2@niplan.com",
            password="TestPassword123!",
        )
        SellerProfile.objects.create(user=user_2, seller_type="INDIVIDUAL")
        self.client.force_authenticate(user=user_2)
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_seller_can_pause_listing(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="To Pause",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-actions", kwargs={"pk": listing.pk})
        response = self.client.post(url, {"action": "pause"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.PAUSED)

    def test_seller_can_archive_listing(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="To Archive",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PAUSED,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-actions", kwargs={"pk": listing.pk})
        response = self.client.post(url, {"action": "archive"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.Status.ARCHIVED)

    def test_update_listing(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Old Title",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.patch(
            url,
            {"title": "New Title", "price": "799.00", "stock": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "New Title")
        self.assertEqual(response.data["price"], "799.00")
        self.assertEqual(response.data["stock"], 5)

    def test_cannot_update_archived_listing(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Archived",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.ARCHIVED,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.patch(url, {"title": "Hack"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_listings(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        response = self.client.get(self.url + "?search=Galaxy")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_category(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        response = self.client.get(self.url + "?category=smartphones")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_min_max_price(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Cheap",
            price=Decimal("500.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Expensive",
            price=Decimal("1500.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        response = self.client.get(self.url + "?min_price=400&max_price=1000")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Cheap")

    def test_ordering_by_price(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="A",
            price=Decimal("1000.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="B",
            price=Decimal("500.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        response = self.client.get(self.url + "?ordering=price")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["title"], "B")

    def test_pagination(self):
        for i in range(25):
            Listing.objects.create(
                seller=self.seller,
                store=self.store,
                variant=self.variant,
                title=f"Phone {i}",
                price=Decimal("100.00"),
                currency="USD",
                stock=10,
                status=Listing.Status.PUBLISHED,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)  # PAGE_SIZE

    def test_my_listings(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Draft",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Published",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:my-listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_my_listings_includes_drafts(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="My Draft",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:my-listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["status"], "DRAFT")

    def test_other_seller_cannot_see_my_listings(self):
        Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Secret",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.DRAFT,
        )
        user_2 = User.objects.create_user(
            email="seller2@niplan.com",
            password="TestPassword123!",
        )
        SellerProfile.objects.create(user=user_2, seller_type="INDIVIDUAL")
        self.client.force_authenticate(user=user_2)
        url = reverse("marketplace:my-listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_cannot_publish_without_stock(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="No Stock",
            price=Decimal("850.00"),
            currency="USD",
            stock=0,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-actions", kwargs={"pk": listing.pk})
        response = self.client.post(url, {"action": "publish"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buyer_cannot_create_listing(self):
        buyer = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=buyer)
        payload = {
            "store": str(self.store.pk),
            "variant": str(self.variant.pk),
            "title": "Hack",
            "price": "100.00",
            "stock": 1,
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_update_published_listing(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Published",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("marketplace:listing-detail", kwargs={"pk": listing.pk})
        response = self.client.patch(url, {"price": "799.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["price"], "799.00")
