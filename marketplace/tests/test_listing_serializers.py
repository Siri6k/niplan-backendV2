# marketplace/tests/test_listing_serializers.py

from decimal import Decimal

from django.test import TestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import (
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductVariant,
    VariantAttributeValue,
)
from marketplace.models import Listing
from marketplace.serializers import (
    ListingActionSerializer,
    ListingCreateSerializer,
    ListingReadSerializer,
)


class ListingSerializerTests(TestCase):
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

        # Attributs pour que display_title soit peuplé
        color_attr = ProductAttribute.objects.create(product=self.product, name="Color")
        storage_attr = ProductAttribute.objects.create(
            product=self.product, name="Storage"
        )
        black = AttributeValue.objects.create(attribute=color_attr, value="Black")
        gb256 = AttributeValue.objects.create(attribute=storage_attr, value="256GB")

        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="SAM-S24-BLK-256",
            is_active=True,
        )
        VariantAttributeValue.objects.create(variant=self.variant, value=black)
        VariantAttributeValue.objects.create(variant=self.variant, value=gb256)

    def test_valid_create_data(self):
        data = {
            "store": str(self.store.pk),
            "variant": str(self.variant.pk),
            "title": "Samsung Galaxy S24",
            "description": "Téléphone neuf",
            "price": "850.00",
            "currency": "USD",
            "condition": "NEW",
            "stock": 10,
            "location": "Kolwezi",
            "is_negotiable": True,
        }
        serializer = ListingCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_seller_is_not_accepted(self):
        data = {
            "seller": str(self.seller.pk),
            "store": str(self.store.pk),
            "variant": str(self.variant.pk),
            "title": "Samsung Galaxy S24",
            "price": "850.00",
            "stock": 10,
        }
        serializer = ListingCreateSerializer(data=data)
        self.assertNotIn("seller", serializer.fields)

    def test_status_is_not_client_controlled(self):
        serializer = ListingCreateSerializer()
        self.assertNotIn("status", serializer.fields)

    def test_invalid_currency(self):
        data = {
            "store": str(self.store.pk),
            "variant": str(self.variant.pk),
            "title": "Samsung Galaxy S24",
            "price": "850.00",
            "currency": "EUR",
            "stock": 10,
        }
        serializer = ListingCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("currency", serializer.errors)

    def test_zero_price(self):
        data = {
            "store": str(self.store.pk),
            "variant": str(self.variant.pk),
            "title": "Samsung Galaxy S24",
            "price": "0.00",
            "stock": 10,
        }
        serializer = ListingCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_negative_price(self):
        data = {
            "store": str(self.store.pk),
            "variant": str(self.variant.pk),
            "title": "Samsung Galaxy S24",
            "price": "-10.00",
            "stock": 10,
        }
        serializer = ListingCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_read_serializer(self):
        listing = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
        )
        serializer = ListingReadSerializer(listing)
        data = serializer.data

        self.assertEqual(data["product_name"], "Samsung Galaxy S24")
        self.assertEqual(data["brand"], "Samsung")
        self.assertEqual(data["sku"], "SAM-S24-BLK-256")
        self.assertEqual(data["store_name"], "Tech Store")
        self.assertEqual(data["seller_name"], "seller@niplan.com")  # full_name fallback

    def test_action_serializer_valid(self):
        serializer = ListingActionSerializer(data={"action": "publish"})
        self.assertTrue(serializer.is_valid())

    def test_action_serializer_invalid(self):
        serializer = ListingActionSerializer(data={"action": "delete"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("action", serializer.errors)
