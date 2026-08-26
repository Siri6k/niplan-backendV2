from decimal import Decimal

from django.db.models import ProtectedError
from django.test import TestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from orders.models import Order, OrderItem


class OrderModelTests(TestCase):

    def setUp(self):
        # -------------------------------------------------
        # BUYER
        # -------------------------------------------------
        self.buyer = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )

        # -------------------------------------------------
        # SELLER
        # -------------------------------------------------
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

        # -------------------------------------------------
        # PRODUCT
        # -------------------------------------------------
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

        # -------------------------------------------------
        # LISTING
        # -------------------------------------------------
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

        # -------------------------------------------------
        # ORDER
        # -------------------------------------------------
        self.order = Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            currency="USD",
            subtotal=Decimal("1700.00"),
            shipping_cost=Decimal("50.00"),
            total=Decimal("1750.00"),
        )

    # =====================================================
    # ORDER
    # =====================================================

    def test_order_creation(self):
        self.assertEqual(self.order.buyer, self.buyer)
        self.assertEqual(self.order.seller, self.seller)
        self.assertEqual(
            self.order.status,
            Order.Status.PENDING,
        )

    def test_order_default_status_is_pending(self):
        self.assertEqual(
            self.order.status,
            Order.Status.PENDING,
        )

    def test_order_string_representation(self):
        self.assertIn(
            str(self.order.id),
            str(self.order),
        )

    def test_order_total_values(self):
        self.assertEqual(
            self.order.subtotal,
            Decimal("1700.00"),
        )
        self.assertEqual(
            self.order.shipping_cost,
            Decimal("50.00"),
        )
        self.assertEqual(
            self.order.total,
            Decimal("1750.00"),
        )

    def test_buyer_can_have_multiple_orders(self):
        Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            currency="USD",
            subtotal=Decimal("100.00"),
            shipping_cost=Decimal("0.00"),
            total=Decimal("100.00"),
        )
        self.assertEqual(
            Order.objects.filter(buyer=self.buyer).count(),
            2,
        )

    # =====================================================
    # ORDER ITEM
    # =====================================================

    def test_order_item_creation(self):
        item = OrderItem.objects.create(
            order=self.order,
            listing=self.listing,
            seller=self.seller,  # Ajouté
            product_name="Samsung Galaxy S24",
            variant_name="256GB Black",
            sku="SAM-S24-BLK-256",
            quantity=2,
            unit_price=Decimal("850.00"),
            subtotal=Decimal("1700.00"),
        )
        self.assertEqual(item.order, self.order)
        self.assertEqual(item.listing, self.listing)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.seller, self.seller)  # Vérification

    def test_order_item_string_representation(self):
        item = OrderItem.objects.create(
            order=self.order,
            listing=self.listing,
            seller=self.seller,  # Ajouté
            product_name="Samsung Galaxy S24",
            quantity=2,
            unit_price=Decimal("850.00"),
            subtotal=Decimal("1700.00"),
        )
        self.assertIn("Samsung Galaxy S24", str(item))

    def test_order_can_have_multiple_items(self):
        OrderItem.objects.create(
            order=self.order,
            listing=self.listing,
            seller=self.seller,  # Ajouté
            product_name="Samsung Galaxy S24",
            quantity=2,
            unit_price=Decimal("850.00"),
            subtotal=Decimal("1700.00"),
        )
        OrderItem.objects.create(
            order=self.order,
            listing=self.listing,
            seller=self.seller,  # Ajouté
            product_name="Samsung Galaxy S24",
            quantity=1,
            unit_price=Decimal("850.00"),
            subtotal=Decimal("850.00"),
        )
        self.assertEqual(self.order.items.count(), 2)

    def test_deleting_order_deletes_items(self):
        item = OrderItem.objects.create(
            order=self.order,
            listing=self.listing,
            seller=self.seller,  # Ajouté
            product_name="Samsung Galaxy S24",
            quantity=1,
            unit_price=Decimal("850.00"),
            subtotal=Decimal("850.00"),
        )
        item_id = item.id
        self.order.delete()
        self.assertFalse(OrderItem.objects.filter(id=item_id).exists())

    def test_deleting_listing_is_protected(self):
        OrderItem.objects.create(
            order=self.order,
            listing=self.listing,
            seller=self.seller,  # Ajouté
            product_name="Samsung Galaxy S24",
            quantity=1,
            unit_price=Decimal("850.00"),
            subtotal=Decimal("850.00"),
        )
        with self.assertRaises(ProtectedError):
            self.listing.delete()
