# cart/tests/test_cart_models.py

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from cart.models import Cart, CartItem


class CartModelTests(TestCase):
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

        # Listing publié
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
    # CART
    # ---------------------------------------------------------

    def test_cart_creation(self):
        cart = Cart.objects.create(buyer=self.buyer)
        self.assertEqual(cart.buyer, self.buyer)
        self.assertEqual(cart.status, Cart.Status.ACTIVE)

    def test_cart_default_status_is_active(self):
        cart = Cart.objects.create(buyer=self.buyer)
        self.assertEqual(cart.status, Cart.Status.ACTIVE)

    def test_cart_string_representation(self):
        cart = Cart.objects.create(buyer=self.buyer)
        self.assertIn(str(cart.id), str(cart))

    def test_buyer_can_have_only_one_active_cart(self):
        Cart.objects.create(buyer=self.buyer, status=Cart.Status.ACTIVE)

        with self.assertRaises(IntegrityError):
            Cart.objects.create(
                buyer=self.buyer,
                status=Cart.Status.ACTIVE,
            )

    def test_buyer_can_have_multiple_non_active_carts(self):
        Cart.objects.create(buyer=self.buyer, status=Cart.Status.CHECKED_OUT)
        Cart.objects.create(buyer=self.buyer, status=Cart.Status.ABANDONED)

        self.assertEqual(Cart.objects.filter(buyer=self.buyer).count(), 2)

    # ---------------------------------------------------------
    # CART ITEM
    # ---------------------------------------------------------

    def test_cart_item_creation(self):
        cart = Cart.objects.create(buyer=self.buyer)
        item = CartItem.objects.create(
            cart=cart,
            listing=self.listing,
            quantity=2,
        )
        self.assertEqual(item.cart, cart)
        self.assertEqual(item.listing, self.listing)
        self.assertEqual(item.quantity, 2)

    def test_cart_item_string_representation(self):
        cart = Cart.objects.create(buyer=self.buyer)
        item = CartItem.objects.create(
            cart=cart,
            listing=self.listing,
            quantity=2,
        )
        # On vérifie que le titre du listing apparaît dans la représentation
        self.assertIn(self.listing.title, str(item))

    def test_same_listing_cannot_be_added_twice_to_same_cart(self):
        cart = Cart.objects.create(buyer=self.buyer)
        CartItem.objects.create(cart=cart, listing=self.listing, quantity=2)

        with self.assertRaises(IntegrityError):
            CartItem.objects.create(
                cart=cart,
                listing=self.listing,
                quantity=3,
            )

    def test_same_listing_can_exist_in_different_carts(self):
        buyer_2 = User.objects.create_user(
            email="buyer2@niplan.com",
            password="TestPassword123!",
        )
        cart_1 = Cart.objects.create(buyer=self.buyer)
        cart_2 = Cart.objects.create(buyer=buyer_2)

        CartItem.objects.create(cart=cart_1, listing=self.listing, quantity=1)
        CartItem.objects.create(cart=cart_2, listing=self.listing, quantity=2)

        self.assertEqual(cart_1.items.count(), 1)
        self.assertEqual(cart_2.items.count(), 1)

    def test_deleting_cart_deletes_cart_items(self):
        cart = Cart.objects.create(buyer=self.buyer)
        item = CartItem.objects.create(cart=cart, listing=self.listing, quantity=2)
        item_id = item.id

        cart.delete()

        self.assertFalse(CartItem.objects.filter(id=item_id).exists())

    def test_deleting_listing_is_protected_when_cart_item_exists(self):
        cart = Cart.objects.create(buyer=self.buyer)
        CartItem.objects.create(cart=cart, listing=self.listing, quantity=1)

        with self.assertRaises(ProtectedError):
            self.listing.delete()
