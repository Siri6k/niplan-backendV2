from decimal import Decimal

from PIL.Image import item
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing
from cart.models import Cart, CartItem


class CartAPITests(APITestCase):

    def setUp(self):

        # -----------------------------------------------------
        # BUYER 1
        # -----------------------------------------------------

        self.buyer = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )

        # -----------------------------------------------------
        # BUYER 2
        # -----------------------------------------------------

        self.buyer_2 = User.objects.create_user(
            email="buyer2@niplan.com",
            password="TestPassword123!",
        )

        # -----------------------------------------------------
        # SELLER
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # PRODUCT
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # LISTING
        # -----------------------------------------------------

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

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    def test_anonymous_user_cannot_access_cart(self):

        response = self.client.get("/api/v1/cart/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # =========================================================
    # GET CART
    # =========================================================

    def test_buyer_can_get_cart(self):

        self.client.force_authenticate(user=self.buyer)

        response = self.client.get("/api/v1/cart/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["status"],
            "ACTIVE",
        )

    def test_get_cart_creates_cart(self):

        self.client.force_authenticate(user=self.buyer)

        self.assertFalse(
            Cart.objects.filter(
                buyer=self.buyer,
                status=Cart.Status.ACTIVE,
            ).exists()
        )

        self.client.get("/api/v1/cart/")

        self.assertTrue(
            Cart.objects.filter(
                buyer=self.buyer,
                status=Cart.Status.ACTIVE,
            ).exists()
        )

    # =========================================================
    # ADD ITEM
    # =========================================================

    def test_buyer_can_add_listing(self):

        self.client.force_authenticate(user=self.buyer)

        response = self.client.post(
            "/api/v1/cart/items/",
            {
                "listing": str(self.listing.id),
                "quantity": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["quantity"],
            2,
        )

        self.assertEqual(
            CartItem.objects.count(),
            1,
        )

    def test_add_same_listing_increases_quantity(self):

        self.client.force_authenticate(user=self.buyer)

        self.client.post(
            "/api/v1/cart/items/",
            {
                "listing": str(self.listing.id),
                "quantity": 2,
            },
            format="json",
        )

        response = self.client.post(
            "/api/v1/cart/items/",
            {
                "listing": str(self.listing.id),
                "quantity": 3,
            },
            format="json",
        )

        # La mise à jour d'un item existant renvoie 200, pas 201
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 5)

    # =========================================================
    # STOCK
    # =========================================================

    def test_cannot_add_more_than_stock(self):

        self.client.force_authenticate(user=self.buyer)

        response = self.client.post(
            "/api/v1/cart/items/",
            {
                "listing": str(self.listing.id),
                "quantity": 11,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =========================================================
    # LISTING STATUS
    # =========================================================

    def test_cannot_add_paused_listing(self):

        self.listing.status = Listing.Status.PAUSED
        self.listing.save()

        self.client.force_authenticate(user=self.buyer)

        response = self.client.post(
            "/api/v1/cart/items/",
            {
                "listing": str(self.listing.id),
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def test_buyer_can_update_quantity(self):

        self.client.force_authenticate(user=self.buyer)

        create_response = self.client.post(
            "/api/v1/cart/items/",
            {
                "listing": str(self.listing.id),
                "quantity": 2,
            },
            format="json",
        )

        item_id = create_response.data["id"]

        response = self.client.patch(
            f"/api/v1/cart/items/{item_id}/",
            {
                "quantity": 5,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["quantity"],
            5,
        )

    # =========================================================
    # DELETE
    # =========================================================

    def test_buyer_can_remove_item(self):

        self.client.force_authenticate(user=self.buyer)

        create_response = self.client.post(
            "/api/v1/cart/items/",
            {
                "listing": str(self.listing.id),
                "quantity": 2,
            },
            format="json",
        )

        item_id = create_response.data["id"]

        response = self.client.delete(f"/api/v1/cart/items/{item_id}/")

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(CartItem.objects.filter(id=item_id).exists())

    # =========================================================
    # SECURITY : BUYER 2
    # =========================================================

    def test_buyer_cannot_modify_another_buyer_item(self):

        cart = Cart.objects.create(buyer=self.buyer)

        item = CartItem.objects.create(
            cart=cart,
            listing=self.listing,
            quantity=2,
        )

        self.client.force_authenticate(user=self.buyer_2)

        response = self.client.patch(
            f"/api/v1/cart/items/{item.id}/",
            {
                "quantity": 5,
            },
            format="json",
        )

        # L'accès à un panier d'un autre utilisateur est interdit (403)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_buyer_cannot_delete_another_buyer_item(self):

        cart = Cart.objects.create(buyer=self.buyer)

        item = CartItem.objects.create(
            cart=cart,
            listing=self.listing,
            quantity=2,
        )

        self.client.force_authenticate(user=self.buyer_2)

        response = self.client.delete(f"/api/v1/cart/items/{item.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(CartItem.objects.filter(id=item.id).exists())

    # =========================================================
    # CLEAR CART
    # =========================================================

    def test_buyer_can_clear_cart(self):

        self.client.force_authenticate(user=self.buyer)

        self.client.post(
            "/api/v1/cart/items/",
            {
                "listing": str(self.listing.id),
                "quantity": 2,
            },
            format="json",
        )

        response = self.client.delete("/api/v1/cart/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        cart = Cart.objects.get(
            buyer=self.buyer,
            status=Cart.Status.ACTIVE,
        )

        self.assertEqual(
            cart.items.count(),
            0,
        )
