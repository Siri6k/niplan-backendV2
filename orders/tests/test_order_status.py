from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from cart.services import CartService
from orders.models import Order, OrderItem


class OrderStatusTests(APITestCase):

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
            sku="SAM-S24-BLK",
            is_active=True,
        )

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

    def create_order(self):
        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )

        self.client.force_authenticate(user=self.buyer)
        response = self.client.post("/api/v1/orders/from-cart/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        return Order.objects.get(id=response.data["id"])

    def test_item_starts_pending(self):
        order = self.create_order()
        item = order.items.first()
        self.assertEqual(item.status, OrderItem.Status.PENDING)

    def test_seller_can_move_item_to_processing(self):
        order = self.create_order()
        item = order.items.first()

        self.client.force_authenticate(user=self.seller_user)
        response = self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "PROCESSING"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, OrderItem.Status.PROCESSING)

    def test_seller_can_ship_item(self):
        order = self.create_order()
        item = order.items.first()

        self.client.force_authenticate(user=self.seller_user)

        # PENDING → PROCESSING
        self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "PROCESSING"},
            format="json",
        )

        # PROCESSING → SHIPPED
        response = self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "SHIPPED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, OrderItem.Status.SHIPPED)

    def test_cannot_skip_status(self):
        order = self.create_order()
        item = order.items.first()

        self.client.force_authenticate(user=self.seller_user)

        # PENDING → DELIVERED (skipping PROCESSING et SHIPPED)
        response = self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "DELIVERED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_seller_cannot_modify_item(self):
        order = self.create_order()
        item = order.items.first()

        other_user = User.objects.create_user(
            email="other-seller@niplan.com",
            password="TestPassword123!",
        )
        SellerProfile.objects.create(
            user=other_user,
            seller_type="INDIVIDUAL",
        )

        self.client.force_authenticate(user=other_user)
        response = self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "PROCESSING"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_status_sync_when_all_items_delivered(self):
        order = self.create_order()
        item = order.items.first()

        self.client.force_authenticate(user=self.seller_user)

        # PENDING → PROCESSING → SHIPPED → DELIVERED
        self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "PROCESSING"},
            format="json",
        )
        self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "SHIPPED"},
            format="json",
        )
        self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "DELIVERED"},
            format="json",
        )

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)

    def test_order_status_sync_when_all_items_cancelled(self):
        order = self.create_order()
        item = order.items.first()

        self.client.force_authenticate(user=self.seller_user)

        # PENDING → CANCELLED
        self.client.patch(
            f"/api/v1/orders/seller/{order.id}/items/{item.id}/status/",
            {"status": "CANCELLED"},
            format="json",
        )

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
