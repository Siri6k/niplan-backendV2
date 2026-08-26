from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import SellerProfile, Store, User
from catalog.models import Category, Product, ProductVariant
from marketplace.models import Listing

from cart.services.cart_service import CartService


class SellerOrderAPITests(APITestCase):

    def setUp(self):
        # BUYER
        self.buyer = User.objects.create_user(
            email="buyer@niplan.com",
            password="TestPassword123!",
        )

        # SELLER A
        seller_user = User.objects.create_user(
            email="seller_a@niplan.com",
            password="TestPassword123!",
        )
        self.seller_user = seller_user
        self.seller = SellerProfile.objects.create(
            user=seller_user,
            seller_type="INDIVIDUAL",
        )
        self.store = Store.objects.create(
            seller=self.seller,
            name="Tech Store",
            slug="tech-store",
            city="Kolwezi",
        )

        # PRODUCT
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
            sku="SAM-S24-BLK-256",
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

    def test_seller_can_see_his_orders(self):
        # Créer une commande en tant qu'acheteur
        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=2)
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post("/api/v1/orders/from-cart/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier que le vendeur voit sa commande
        self.client.force_authenticate(user=self.seller_user)
        response = self.client.get("/api/v1/orders/seller/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(len(response.data[0]["items"]), 1)

    def test_seller_can_view_his_order_detail(self):
        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        self.client.force_authenticate(user=self.buyer)
        create_resp = self.client.post("/api/v1/orders/from-cart/")
        order_id = create_resp.data["id"]

        self.client.force_authenticate(user=self.seller_user)
        response = self.client.get(f"/api/v1/orders/seller/{order_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], order_id)

    def test_random_user_cannot_view_seller_order(self):
        CartService.add_item(buyer=self.buyer, listing=self.listing, quantity=1)
        self.client.force_authenticate(user=self.buyer)
        create_resp = self.client.post("/api/v1/orders/from-cart/")
        order_id = create_resp.data["id"]

        other_user = User.objects.create_user(
            email="random@niplan.com",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get(f"/api/v1/orders/seller/{order_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
