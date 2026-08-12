# catalog/tests/test_product.py

from django.db.models.deletion import ProtectedError
from django.test import TestCase

from catalog.models import Category, Product


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
        )

    def test_create_product(self):
        product = Product.objects.create(
            category=self.category,
            name="Samsung Galaxy S24",
            brand="Samsung",
            model="Galaxy S24",
            slug="samsung-galaxy-s24",
            description="Smartphone haut de gamme Samsung.",
        )

        self.assertEqual(product.name, "Samsung Galaxy S24")
        self.assertEqual(product.brand, "Samsung")
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.status, Product.Status.DRAFT)
        self.assertTrue(product.is_active)

    def test_product_specifications(self):
        product = Product.objects.create(
            category=self.category,
            name="Samsung Galaxy S24",
            brand="Samsung",
            model="Galaxy S24",
            slug="samsung-galaxy-s24",
            specifications={
                "ram": "8GB",
                "storage": "256GB",
                "network": "5G",
                "screen_size": '6.2"',
            },
        )

        self.assertEqual(product.specifications["ram"], "8GB")
        self.assertEqual(product.specifications["storage"], "256GB")

    def test_category_products_relation(self):
        product = Product.objects.create(
            category=self.category,
            name="Samsung Galaxy S24",
            brand="Samsung",
            slug="samsung-galaxy-s24",
        )

        self.assertIn(product, self.category.products.all())

    def test_category_with_products_is_protected(self):
        Product.objects.create(
            category=self.category,
            name="Samsung Galaxy S24",
            brand="Samsung",
            slug="samsung-galaxy-s24",
        )

        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_product_slug_must_be_unique(self):
        Product.objects.create(
            category=self.category,
            name="Samsung Galaxy S24",
            slug="samsung-galaxy-s24",
        )

        with self.assertRaises(Exception):
            Product.objects.create(
                category=self.category,
                name="Another Product",
                slug="samsung-galaxy-s24",
            )

    def test_product_status(self):
        product = Product.objects.create(
            category=self.category,
            name="Samsung Galaxy S24",
            slug="samsung-galaxy-s24",
            status=Product.Status.ACTIVE,
        )

        self.assertEqual(product.status, Product.Status.ACTIVE)

        product.status = Product.Status.ARCHIVED
        product.save()
        product.refresh_from_db()

        self.assertEqual(product.status, Product.Status.ARCHIVED)

    def test_display_name_with_brand(self):
        product = Product.objects.create(
            category=self.category,
            name="Galaxy S24",
            brand="Samsung",
            slug="samsung-galaxy-s24",
        )
        self.assertEqual(product.display_name, "Samsung Galaxy S24")

    def test_display_name_without_brand(self):
        product = Product.objects.create(
            category=self.category,
            name="Generic Charger",
            slug="generic-charger",
        )
        self.assertEqual(product.display_name, "Generic Charger")
