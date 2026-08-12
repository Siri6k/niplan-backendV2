# catalog/tests/test_api.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import (
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductMedia,
    ProductVariant,
    VariantAttributeValue,
)


class CatalogAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
        )
        self.child_cat = Category.objects.create(
            name="Android",
            slug="android",
            parent=self.category,
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Galaxy S24",
            brand="Samsung",
            slug="samsung-galaxy-s24",
            status=Product.Status.ACTIVE,
            specifications={"ram": "8GB"},
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="S24-256-BLK",
        )
        self.media = ProductMedia.objects.create(
            product=self.product,
            url="https://example.com/s24.jpg",
            is_primary=True,
        )

    def test_category_list(self):
        url = reverse("catalog:category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Smartphones")

    def test_category_detail(self):
        url = reverse("catalog:category-detail", kwargs={"slug": "smartphones"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Smartphones")

    def test_product_list(self):
        url = reverse("catalog:product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Galaxy S24")

    def test_product_list_filter_by_brand(self):
        url = reverse("catalog:product-list") + "?brand=Samsung"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_product_list_search(self):
        url = reverse("catalog:product-list") + "?search=Galaxy"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_product_detail(self):
        url = reverse("catalog:product-detail", kwargs={"slug": "samsung-galaxy-s24"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Galaxy S24")
        self.assertIn("variants", response.data)
        self.assertIn("media", response.data)
        self.assertIn("specifications", response.data)

    def test_variant_detail(self):
        url = reverse("catalog:variant-detail", kwargs={"sku": "S24-256-BLK"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sku"], "S24-256-BLK")
        self.assertIn("display_title", response.data)
