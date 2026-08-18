# cart/tests/test_cart_service.py

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from cart.models import Cart, CartItem
from cart.services.cart_service import CartService

from decimal import Decimal


class CartServiceTests(TestCase):
    def setUp(self):
        # Buyer
        self.buyer = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )

        # Seller
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

        # Catalogue
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

        # Listing
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

    # ---------------------------------------------------------
    # GET / CREATE CART
    # ---------------------------------------------------------

    def test_get_or_create_active_cart(self):
        cart = CartService.get_or_create_active_cart(buyer=self.buyer)
        self.assertEqual(cart.buyer, self.buyer)
        self.assertEqual(cart.status, Cart.Status.ACTIVE)

    def test_get_or_create_returns_same_cart(self):
        cart_1 = CartService.get_or_create_active_cart(buyer=self.buyer)
        cart_2 = CartService.get_or_create_active_cart(buyer=self.buyer)
        self.assertEqual(cart_1.id, cart_2.id)
        self.assertEqual(
            Cart.objects.filter(
                buyer=self.buyer,
                status=Cart.Status.ACTIVE,
            ).count(),
            1,
        )

    # ---------------------------------------------------------
    # ADD ITEM
    # ---------------------------------------------------------

    def test_add_item(self):
        item = CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.listing, self.listing)
        self.assertEqual(item.cart.buyer, self.buyer)

    def test_add_same_listing_increases_quantity(self):
        item_1 = CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        item_2 = CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=3,
        )
        self.assertEqual(item_1.id, item_2.id)
        self.assertEqual(item_2.quantity, 5)

    def test_add_item_cannot_exceed_stock(self):
        with self.assertRaises(ValidationError):
            CartService.add_item(
                buyer=self.buyer,
                listing=self.listing,
                quantity=11,
            )

    def test_add_existing_item_cannot_exceed_stock(self):

        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=7,
        )
        with self.assertRaises(ValidationError):
            CartService.add_item(
                buyer=self.buyer,
                listing=self.listing,
                quantity=4,
            )

    def test_cannot_add_unpublished_listing(self):
        self.listing.status = Listing.Status.PAUSED
        self.listing.save()
        with self.assertRaises(ValidationError):
            CartService.add_item(
                buyer=self.buyer,
                listing=self.listing,
                quantity=1,
            )

    def test_cannot_add_out_of_stock_listing(self):
        self.listing.stock = 0
        self.listing.save()
        with self.assertRaises(ValidationError):
            CartService.add_item(
                buyer=self.buyer,
                listing=self.listing,
                quantity=1,
            )

    def test_quantity_must_be_positive(self):
        with self.assertRaises(ValidationError):
            CartService.add_item(
                buyer=self.buyer,
                listing=self.listing,
                quantity=0,
            )

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def test_update_item_quantity(self):
        item = CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        updated = CartService.update_item_quantity(
            buyer=self.buyer,
            item=item,
            quantity=5,
        )
        self.assertEqual(updated.quantity, 5)

    def test_update_quantity_cannot_exceed_stock(self):
        item = CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        with self.assertRaises(ValidationError):
            CartService.update_item_quantity(
                buyer=self.buyer,
                item=item,
                quantity=11,
            )

    # ---------------------------------------------------------
    # REMOVE
    # ---------------------------------------------------------

    def test_remove_item(self):
        item = CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        CartService.remove_item(buyer=self.buyer, item=item)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    # ---------------------------------------------------------
    # CLEAR
    # ---------------------------------------------------------

    def test_clear_cart(self):
        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        CartService.clear_cart(buyer=self.buyer)
        cart = Cart.objects.get(buyer=self.buyer, status=Cart.Status.ACTIVE)
        self.assertEqual(cart.items.count(), 0)

    # ---------------------------------------------------------
    # TOTAL
    # ---------------------------------------------------------

    def test_cart_total(self):
        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        cart = Cart.objects.get(buyer=self.buyer, status=Cart.Status.ACTIVE)
        total = CartService.get_cart_total(cart=cart)
        self.assertEqual(total, Decimal("1700.00"))

    # ---------------------------------------------------------
    # VALIDATE CART
    # ---------------------------------------------------------

    def test_validate_cart(self):
        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        cart = Cart.objects.get(buyer=self.buyer, status=Cart.Status.ACTIVE)
        self.assertTrue(CartService.validate_cart(cart=cart))

    def test_validate_cart_detects_stock_change(self):
        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=8,
        )
        self.listing.stock = 5
        self.listing.save()
        cart = Cart.objects.get(buyer=self.buyer, status=Cart.Status.ACTIVE)
        with self.assertRaises(ValidationError):
            CartService.validate_cart(cart=cart)

    def test_validate_cart_detects_paused_listing(self):
        CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=1,
        )
        self.listing.status = Listing.Status.PAUSED
        self.listing.save()
        cart = Cart.objects.get(buyer=self.buyer, status=Cart.Status.ACTIVE)
        with self.assertRaises(ValidationError):
            CartService.validate_cart(cart=cart)

    def test_cart_cannot_have_multiple_currencies(self):
        # Créer un second listing en EUR
        listing_eur = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24 (EUR)",
            price=Decimal("800.00"),
            currency="EUR",
            stock=5,
            status=Listing.Status.PUBLISHED,
        )

        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        with self.assertRaises(ValidationError):
            CartService.add_item(buyer=self.buyer, listing=listing_eur, quantity=1)

    def test_clean_cart_removes_unavailable_listings(self):
        # Ajouter un item
        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=2)

        # Rendre le listing non publié
        self.listing.status = Listing.Status.PAUSED
        self.listing.save()

        cart = CartService.get_active_cart_with_items(buyer=self.buyer)
        CartService.clean_cart(cart=cart)

        # Recharger le panier depuis la base pour obtenir l'état réel
        cart = Cart.objects.get(pk=cart.pk)

        self.assertEqual(cart.items.count(), 0)
