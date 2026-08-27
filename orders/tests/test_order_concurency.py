from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import transaction

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from cart.models import Cart, CartItem
from orders.models import Order
from orders.services.order_service import OrderService


class OrderConcurrencyTests(TestCase):

    def setUp(self):
        self.buyer1 = User.objects.create_user(email="buyer1@test.com", password="pass")
        self.buyer2 = User.objects.create_user(email="buyer2@test.com", password="pass")

        seller_user = User.objects.create_user(email="seller@test.com", password="pass")
        seller = SellerProfile.objects.create(
            user=seller_user, seller_type="INDIVIDUAL"
        )
        store = Store.objects.create(
            seller=seller, name="Store", slug="store", city="Ville"
        )
        category = Category.objects.create(name="Cat", slug="cat")
        product = Product.objects.create(
            category=category,
            name="Prod",
            brand="Brand",
            model="Model",
            slug="prod",
            status=Product.Status.ACTIVE,
        )
        variant = ProductVariant.objects.create(
            product=product, sku="SKU", is_active=True
        )
        self.listing = Listing.objects.create(
            seller=seller,
            store=store,
            variant=variant,
            title="Article unique",
            price=Decimal("100.00"),
            currency="USD",
            stock=1,
            status=Listing.Status.PUBLISHED,
        )

    def test_only_one_buyer_can_buy_last_stock(self):
        # Préparer les paniers
        cart1 = Cart.objects.create(buyer=self.buyer1, status=Cart.Status.ACTIVE)
        CartItem.objects.create(cart=cart1, listing=self.listing, quantity=1)

        cart2 = Cart.objects.create(buyer=self.buyer2, status=Cart.Status.ACTIVE)
        CartItem.objects.create(cart=cart2, listing=self.listing, quantity=1)

        # Premier acheteur (succès)
        with transaction.atomic():
            orders1 = OrderService.create_orders_from_cart(buyer=self.buyer1)
            self.assertEqual(len(orders1), 1)
            self.assertEqual(orders1[0].status, Order.Status.PENDING)
            self.listing.refresh_from_db()
            self.assertEqual(self.listing.stock, 0)
            self.assertEqual(self.listing.status, Listing.Status.SOLD_OUT)

        # Deuxième acheteur (doit échouer)
        with self.assertRaises(ValidationError):
            with transaction.atomic():
                OrderService.create_orders_from_cart(buyer=self.buyer2)

        # Le stock reste à 0 et le statut SOLD_OUT
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.stock, 0)
        self.assertEqual(self.listing.status, Listing.Status.SOLD_OUT)
