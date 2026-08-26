from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing

from cart.services import CartService
from orders.models import Order, OrderItem


class OrderAPITests(APITestCase):

    def setUp(self):
        # BUYER
        self.buyer = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )
        self.other_buyer = User.objects.create_user(
            email="other@niplan.com",
            password="TestPassword123!",
        )

        # SELLER
        seller_user = User.objects.create_user(
            email="seller@niplan.com",
            password="TestPassword123!",
        )
        self.seller = SellerProfile.objects.create(
            user=seller_user,
            seller_type="INDIVIDUAL",
        )
        self.store = Store.objects.create(
            seller=self.seller,
            name="Tech Store",
            slug="tech-store",
            city="Kolwezi",
        )

        # PRODUCT
        category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
        )
        product = Product.objects.create(
            category=category,
            name="Samsung Galaxy S24",
            brand="Samsung",
            model="Galaxy S24",
            slug="samsung-galaxy-s24",
            status=Product.Status.ACTIVE,
        )
        variant = ProductVariant.objects.create(
            product=product,
            sku="SAM-S24-BLK-256",
            is_active=True,
        )

        # LISTING
        self.listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )

    # ---------------------------------------------------------
    # AUTH
    # ---------------------------------------------------------
    def test_anonymous_user_cannot_access_orders(self):
        response = self.client.get("/api/v1/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---------------------------------------------------------
    # CREATE ORDER FROM CART
    # ---------------------------------------------------------
    def test_buyer_can_create_order_from_cart(self):
        self.client.force_authenticate(user=self.buyer)

        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )

        response = self.client.post("/api/v1/orders/from-cart/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Order.Status.PENDING)
        self.assertEqual(response.data["total"], "1700.00")

    # ---------------------------------------------------------
    # LIST ORDERS
    # ---------------------------------------------------------
    def test_buyer_can_list_orders(self):
        self.client.force_authenticate(user=self.buyer)

        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        self.client.post("/api/v1/orders/from-cart/")

        response = self.client.get("/api/v1/orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # ---------------------------------------------------------
    # DETAIL
    # ---------------------------------------------------------
    def test_buyer_can_view_order(self):
        self.client.force_authenticate(user=self.buyer)

        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        create_response = self.client.post("/api/v1/orders/from-cart/")
        order_id = create_response.data["id"]

        response = self.client.get(f"/api/v1/orders/{order_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], order_id)

    # ---------------------------------------------------------
    # SECURITY
    # ---------------------------------------------------------
    def test_buyer_cannot_view_another_buyer_order(self):
        self.client.force_authenticate(user=self.buyer)
        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        create_response = self.client.post("/api/v1/orders/from-cart/")
        order_id = create_response.data["id"]

        self.client.force_authenticate(user=self.other_buyer)
        response = self.client.get(f"/api/v1/orders/{order_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------------------------------------------------------
    # CANCEL
    # ---------------------------------------------------------
    def test_buyer_can_cancel_order(self):
        self.client.force_authenticate(user=self.buyer)

        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=2)
        create_response = self.client.post("/api/v1/orders/from-cart/")
        order_id = create_response.data["id"]

        response = self.client.post(f"/api/v1/orders/{order_id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Order.Status.CANCELLED)

    # ---------------------------------------------------------
    # MULTI-SELLER (optionnel)
    # ---------------------------------------------------------
    def test_cart_with_two_sellers_creates_two_orders(self):
        # Créer un second vendeur et son listing
        seller2_user = User.objects.create_user(
            email="seller2@niplan.com",
            password="TestPassword123!",
        )
        seller2 = SellerProfile.objects.create(
            user=seller2_user,
            seller_type="INDIVIDUAL",
        )
        store2 = Store.objects.create(
            seller=seller2,
            name="Phone Shop",
            slug="phone-shop",
            city="Lubumbashi",
        )
        product2 = Product.objects.create(
            category=Category.objects.first(),
            name="iPhone 15",
            brand="Apple",
            model="iPhone 15",
            slug="iphone-15",
            status=Product.Status.ACTIVE,
        )
        variant2 = ProductVariant.objects.create(
            product=product2,
            sku="APL-15-BLK-128",
            is_active=True,
        )
        listing2 = Listing.objects.create(
            seller=seller2,
            store=store2,
            variant=variant2,
            title="iPhone 15",
            price=Decimal("900.00"),
            currency="USD",
            stock=5,
            status=Listing.Status.PUBLISHED,
        )

        self.client.force_authenticate(user=self.buyer)
        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        CartService.add_item(buyer=self.buyer, listing=listing2, quantity=1)

        response = self.client.post("/api/v1/orders/from-cart/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 2)

        # Vérifier les totaux sans se soucier de l'ordre
        totals = [order["total"] for order in response.data]
        self.assertIn("850.00", totals)
        self.assertIn("900.00", totals)
