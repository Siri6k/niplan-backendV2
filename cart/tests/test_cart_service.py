# cart/tests/test_cart_service.py

from decimal import Decimal
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from cart.models import Cart, CartItem
from cart.services import CartService


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
        item, _ = CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.listing, self.listing)
        self.assertEqual(item.cart.buyer, self.buyer)

    def test_add_same_listing_increases_quantity(self):
        item_1, _ = CartService.add_item(
            buyer=self.buyer,
            listing=self.listing,
            quantity=2,
        )
        item_2, _ = CartService.add_item(
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
        item, _ = CartService.add_item(
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
        item, _ = CartService.add_item(
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
        item, _ = CartService.add_item(
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
        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=2)
        self.listing.status = Listing.Status.PAUSED
        self.listing.save()

        cart = CartService.get_active_cart_with_items(buyer=self.buyer)
        CartService.clean_cart(cart=cart)

        cart = Cart.objects.get(pk=cart.pk)
        self.assertEqual(cart.items.count(), 0)

    def test_mark_abandoned_changes_status(self):
        cart = CartService.get_or_create_active_cart(buyer=self.buyer)
        self.assertEqual(cart.status, Cart.Status.ACTIVE)

        CartService.mark_abandoned(cart=cart)
        cart.refresh_from_db()
        self.assertEqual(cart.status, Cart.Status.ABANDONED)

    def test_mark_abandoned_does_not_affect_checked_out_cart(self):
        checked_out_cart = Cart.objects.create(
            buyer=self.buyer,
            status=Cart.Status.CHECKED_OUT,
        )
        CartService.mark_abandoned(cart=checked_out_cart)
        checked_out_cart.refresh_from_db()
        self.assertEqual(checked_out_cart.status, Cart.Status.CHECKED_OUT)

    def test_last_accessed_at_updated_on_operations(self):
        cart = CartService.get_or_create_active_cart(buyer=self.buyer)
        initial_access = cart.last_accessed_at

        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        cart.refresh_from_db()
        self.assertGreater(cart.last_accessed_at, initial_access)

        item = cart.items.first()
        old_access = cart.last_accessed_at
        CartService.update_item_quantity(buyer=self.buyer, item=item, quantity=2)
        cart.refresh_from_db()
        self.assertGreater(cart.last_accessed_at, old_access)

        old_access = cart.last_accessed_at
        CartService.remove_item(buyer=self.buyer, item=item)
        cart.refresh_from_db()
        self.assertGreater(cart.last_accessed_at, old_access)

        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        cart.refresh_from_db()
        old_access = cart.last_accessed_at
        CartService.clear_cart(buyer=self.buyer)
        cart.refresh_from_db()
        self.assertGreater(cart.last_accessed_at, old_access)

    def test_get_active_cart_with_items_touches_last_accessed(self):
        cart = CartService.get_or_create_active_cart(buyer=self.buyer)
        old_access = cart.last_accessed_at
        cart.last_accessed_at = timezone.now() - timedelta(seconds=10)
        cart.save(update_fields=["last_accessed_at"])
        cart.refresh_from_db()
        self.assertLess(cart.last_accessed_at, old_access)

        CartService.get_active_cart_with_items(buyer=self.buyer)
        cart.refresh_from_db()
        self.assertGreater(cart.last_accessed_at, old_access)

    # Nouveaux tests pour clean_cart et validation des devises
    def test_clean_cart_reduces_quantity_when_stock_decreases(self):
        cart = Cart.objects.create(buyer=self.buyer, status=Cart.Status.ACTIVE)
        item = CartItem.objects.create(cart=cart, listing=self.listing, quantity=8)
        self.listing.stock = 5
        self.listing.save()

        CartService.clean_cart(cart=cart)

        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_clean_cart_removes_item_when_listing_is_out_of_stock(self):
        cart = Cart.objects.create(buyer=self.buyer, status=Cart.Status.ACTIVE)
        item = CartItem.objects.create(cart=cart, listing=self.listing, quantity=5)
        self.listing.stock = 0
        self.listing.save()

        CartService.clean_cart(cart=cart)

        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_clean_cart_removes_unpublished_listing(self):
        cart = Cart.objects.create(buyer=self.buyer, status=Cart.Status.ACTIVE)
        item = CartItem.objects.create(cart=cart, listing=self.listing, quantity=5)
        self.listing.status = Listing.Status.DRAFT
        self.listing.save()

        CartService.clean_cart(cart=cart)

        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_validate_cart_rejects_multiple_currencies(self):
        listing2 = Listing.objects.create(
            seller=self.seller,
            store=self.store,
            variant=self.variant,
            title="Samsung Galaxy S24 (EUR)",
            price=Decimal("800.00"),
            currency="EUR",
            stock=5,
            status=Listing.Status.PUBLISHED,
        )
        cart = Cart.objects.create(buyer=self.buyer, status=Cart.Status.ACTIVE)
        CartItem.objects.create(cart=cart, listing=self.listing, quantity=1)
        CartItem.objects.create(cart=cart, listing=listing2, quantity=1)

        with self.assertRaises(ValidationError) as cm:
            CartService.validate_cart(cart=cart)
        self.assertIn("même devise", str(cm.exception))

    def test_seller_cannot_add_own_listing_to_cart(self):
        with self.assertRaises(ValidationError):
            CartService.add_item(
                buyer=self.seller_user,
                listing=self.listing,
                quantity=1,
            )
