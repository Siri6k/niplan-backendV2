from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing

from cart.models import Cart, CartItem
from cart.services.cart_service import CartService

from orders.models import Order, OrderItem
from orders.services.order_service import OrderService


class OrderServiceTests(TestCase):

    def setUp(self):
        # BUYER
        self.buyer = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )

        # SELLER 1
        seller_user1 = User.objects.create_user(
            email="seller1@niplan.com",
            password="TestPassword123!",
        )
        self.seller1 = SellerProfile.objects.create(
            user=seller_user1,
            seller_type="INDIVIDUAL",
        )
        self.store1 = Store.objects.create(
            seller=self.seller1,
            name="Tech Store",
            slug="tech-store",
            city="Kolwezi",
        )

        # SELLER 2
        seller_user2 = User.objects.create_user(
            email="seller2@niplan.com",
            password="TestPassword123!",
        )
        self.seller2 = SellerProfile.objects.create(
            user=seller_user2,
            seller_type="INDIVIDUAL",
        )
        self.store2 = Store.objects.create(
            seller=self.seller2,
            name="Phone Shop",
            slug="phone-shop",
            city="Lubumbashi",
        )

        # PRODUCTS
        category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
        )
        product1 = Product.objects.create(
            category=category,
            name="Samsung Galaxy S24",
            brand="Samsung",
            model="Galaxy S24",
            slug="samsung-galaxy-s24",
            status=Product.Status.ACTIVE,
        )
        variant1 = ProductVariant.objects.create(
            product=product1,
            sku="SAM-S24-BLK-256",
            is_active=True,
        )

        product2 = Product.objects.create(
            category=category,
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

        # LISTINGS
        self.listing1 = Listing.objects.create(
            seller=self.seller1,
            store=self.store1,
            variant=variant1,
            title="Samsung Galaxy S24",
            price=Decimal("850.00"),
            currency="USD",
            stock=10,
            status=Listing.Status.PUBLISHED,
        )

        self.listing2 = Listing.objects.create(
            seller=self.seller2,
            store=self.store2,
            variant=variant2,
            title="iPhone 15",
            price=Decimal("900.00"),
            currency="USD",
            stock=5,
            status=Listing.Status.PUBLISHED,
        )

    def test_create_orders_from_cart_single_seller(self):
        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing1,
            quantity=2,
        )

        orders = OrderService.create_orders_from_cart(buyer=self.buyer)

        self.assertEqual(len(orders), 1)
        order = orders[0]
        self.assertEqual(order.buyer, self.buyer)
        self.assertEqual(order.seller, self.seller1)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.subtotal, Decimal("1700.00"))
        self.assertEqual(order.total, Decimal("1700.00"))

        item = order.items.first()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal("850.00"))
        self.assertEqual(item.subtotal, Decimal("1700.00"))
        self.assertEqual(item.seller, self.seller1)

        # Vérifier le stock
        self.listing1.refresh_from_db()
        self.assertEqual(self.listing1.stock, 8)

        # Panier marqué CHECKED_OUT
        cart = Cart.objects.get(buyer=self.buyer, status=Cart.Status.CHECKED_OUT)
        self.assertIsNotNone(cart)

    def test_create_orders_from_cart_multiple_sellers(self):
        CartService.add_item(buyer=self.buyer, listing=self.listing1, quantity=1)
        CartService.add_item(buyer=self.buyer, listing=self.listing2, quantity=1)

        orders = OrderService.create_orders_from_cart(buyer=self.buyer)

        self.assertEqual(len(orders), 2)

        # Commande 1 : seller1
        order1 = next(o for o in orders if o.seller == self.seller1)
        self.assertEqual(order1.subtotal, Decimal("850.00"))
        self.assertEqual(order1.items.count(), 1)
        self.assertEqual(order1.items.first().listing, self.listing1)

        # Commande 2 : seller2
        order2 = next(o for o in orders if o.seller == self.seller2)
        self.assertEqual(order2.subtotal, Decimal("900.00"))
        self.assertEqual(order2.items.count(), 1)
        self.assertEqual(order2.items.first().listing, self.listing2)

        # Stocks diminués
        self.listing1.refresh_from_db()
        self.listing2.refresh_from_db()
        self.assertEqual(self.listing1.stock, 9)
        self.assertEqual(self.listing2.stock, 4)

        # Panier CHECKED_OUT
        cart = Cart.objects.get(buyer=self.buyer, status=Cart.Status.CHECKED_OUT)
        self.assertIsNotNone(cart)

    def test_empty_cart_raises_error(self):
        with self.assertRaises(ValidationError) as cm:
            OrderService.create_orders_from_cart(buyer=self.buyer)
        self.assertIn("Aucun panier actif", str(cm.exception))

    def test_cancel_order_restores_stock(self):
        CartService.add_item(buyer=self.buyer, listing=self.listing1, quantity=3)
        orders = OrderService.create_orders_from_cart(buyer=self.buyer)
        order = orders[0]

        self.listing1.refresh_from_db()
        self.assertEqual(self.listing1.stock, 7)

        OrderService.cancel_order(buyer=self.buyer, order_id=order.id)

        self.listing1.refresh_from_db()
        self.assertEqual(self.listing1.stock, 10)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)

    def test_cannot_cancel_delivered_order(self):
        CartService.add_item(buyer=self.buyer, listing=self.listing1, quantity=1)
        order = OrderService.create_orders_from_cart(buyer=self.buyer)[0]
        order.status = Order.Status.DELIVERED
        order.save()

        with self.assertRaises(ValidationError):
            OrderService.cancel_order(buyer=self.buyer, order_id=order.id)

    def test_get_order_ownership(self):
        CartService.add_item(buyer=self.buyer, listing=self.listing1, quantity=1)
        order = OrderService.create_orders_from_cart(buyer=self.buyer)[0]

        other_buyer = User.objects.create_user(
            email="other@niplan.com",
            password="TestPassword123!",
        )
        result = OrderService.get_order(buyer=other_buyer, order_id=order.id)
        self.assertIsNone(result)

        result = OrderService.get_order(buyer=self.buyer, order_id=order.id)
        self.assertEqual(result, order)

    def test_update_status_transitions(self):
        CartService.add_item(buyer=self.buyer, listing=self.listing1, quantity=1)
        order = OrderService.create_orders_from_cart(buyer=self.buyer)[0]

        # PENDING -> CONFIRMED
        OrderService.update_status(order=order, new_status=Order.Status.CONFIRMED)
        self.assertEqual(order.status, Order.Status.CONFIRMED)

        # CONFIRMED -> PROCESSING
        OrderService.update_status(order=order, new_status=Order.Status.PROCESSING)
        self.assertEqual(order.status, Order.Status.PROCESSING)

        # PROCESSING -> SHIPPED
        OrderService.update_status(order=order, new_status=Order.Status.SHIPPED)
        self.assertEqual(order.status, Order.Status.SHIPPED)

        # SHIPPED -> DELIVERED
        OrderService.update_status(order=order, new_status=Order.Status.DELIVERED)
        self.assertEqual(order.status, Order.Status.DELIVERED)

        # Tentative invalide : DELIVERED -> SHIPPED
        with self.assertRaises(ValidationError):
            OrderService.update_status(order=order, new_status=Order.Status.SHIPPED)
