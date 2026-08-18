# cart/tests/test_cart_serializers.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from cart.models import Cart, CartItem
from cart.serializers import (
    CartReadSerializer,
    CartItemCreateSerializer,
    CartItemReadSerializer,
    CartItemUpdateSerializer,
)


class CartSerializerTests(TestCase):
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
            status=Product.Status.ACTIVE,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="SAM-S24-BLK-256",
            is_active=True,
        )
        self.listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )
        self.cart = Cart.objects.create(buyer=self.buyer)
        self.item = CartItem.objects.create(
            cart=self.cart,
            listing=self.listing,
            quantity=2,
        )

    def test_create_serializer_valid(self):
        serializer = CartItemCreateSerializer(
            data={
                "listing": str(self.listing.id),
                "quantity": 2,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_serializer_rejects_zero_quantity(self):
        serializer = CartItemCreateSerializer(
            data={
                "listing": str(self.listing.id),
                "quantity": 0,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_update_serializer_valid(self):
        serializer = CartItemUpdateSerializer(data={"quantity": 5})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_read_serializer(self):
        serializer = CartItemReadSerializer(self.item)
        data = serializer.data

        self.assertEqual(data["product_name"], "Samsung Galaxy S24")
        self.assertEqual(data["brand"], "Samsung")
        self.assertEqual(data["sku"], "SAM-S24-BLK-256")
        self.assertEqual(data["seller_name"], "Tech Store")
        self.assertEqual(data["unit_price"], "850.00")
        self.assertEqual(data["quantity"], 2)
        self.assertEqual(data["subtotal"], Decimal("1700.00"))

    def test_cart_read_serializer(self):
        serializer = CartReadSerializer(self.cart)
        data = serializer.data

        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["item_count"], 2)
        self.assertEqual(data["total"], Decimal("1700.00"))
        self.assertEqual(len(data["items"]), 1)
