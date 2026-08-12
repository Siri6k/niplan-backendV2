# catalog/tests/test_variant.py

from django.db.models.deletion import ProtectedError
from django.test import TestCase

from catalog.models import (
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductVariant,
    VariantAttributeValue,
)


class VariantModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Galaxy S24",
            brand="Samsung",
            slug="samsung-galaxy-s24",
        )

    def test_create_product_attribute(self):
        attr = ProductAttribute.objects.create(
            product=self.product,
            name="Color",
        )
        self.assertEqual(attr.name, "Color")
        self.assertEqual(attr.product, self.product)

    def test_create_attribute_value(self):
        attr = ProductAttribute.objects.create(
            product=self.product,
            name="Storage",
        )
        value = AttributeValue.objects.create(
            attribute=attr,
            value="256GB",
        )
        self.assertEqual(value.value, "256GB")
        self.assertEqual(value.attribute, attr)

    def test_create_product_variant(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            sku="S24-256-BLK",
        )
        self.assertEqual(variant.product, self.product)
        self.assertEqual(variant.sku, "S24-256-BLK")
        self.assertTrue(variant.is_active)

    def test_variant_with_attribute_values(self):
        color_attr = ProductAttribute.objects.create(
            product=self.product,
            name="Color",
        )
        storage_attr = ProductAttribute.objects.create(
            product=self.product,
            name="Storage",
        )

        black = AttributeValue.objects.create(attribute=color_attr, value="Black")
        storage256 = AttributeValue.objects.create(
            attribute=storage_attr, value="256GB"
        )

        variant = ProductVariant.objects.create(
            product=self.product,
            sku="S24-256-BLK",
        )

        VariantAttributeValue.objects.create(variant=variant, value=black)
        VariantAttributeValue.objects.create(variant=variant, value=storage256)

        self.assertEqual(variant.variant_values.count(), 2)
        self.assertIn(black, [v.value for v in variant.variant_values.all()])
        self.assertIn(storage256, [v.value for v in variant.variant_values.all()])

    def test_sku_must_be_unique(self):
        ProductVariant.objects.create(
            product=self.product,
            sku="S24-256-BLK",
        )
        with self.assertRaises(Exception):
            ProductVariant.objects.create(
                product=self.product,
                sku="S24-256-BLK",
            )

    def test_product_is_protected_when_variants_exist(self):
        ProductVariant.objects.create(
            product=self.product,
            sku="S24-256-BLK",
        )
        with self.assertRaises(ProtectedError):
            self.product.delete()

    def test_attribute_summary(self):
        color_attr = ProductAttribute.objects.create(product=self.product, name="Color")
        storage_attr = ProductAttribute.objects.create(
            product=self.product, name="Storage"
        )

        black = AttributeValue.objects.create(attribute=color_attr, value="Black")
        storage256 = AttributeValue.objects.create(
            attribute=storage_attr, value="256GB"
        )

        variant = ProductVariant.objects.create(product=self.product, sku="S24-256-BLK")
        VariantAttributeValue.objects.create(variant=variant, value=black)
        VariantAttributeValue.objects.create(variant=variant, value=storage256)

        self.assertEqual(variant.attribute_summary, "Color: Black / Storage: 256GB")

    def test_display_title(self):
        color_attr = ProductAttribute.objects.create(product=self.product, name="Color")
        black = AttributeValue.objects.create(attribute=color_attr, value="Black")

        variant = ProductVariant.objects.create(product=self.product, sku="S24-BLK")
        VariantAttributeValue.objects.create(variant=variant, value=black)

        self.assertEqual(variant.display_title, "Samsung Galaxy S24 — Color: Black")

    def test_duplicate_attribute_value_on_variant_fails(self):
        color_attr = ProductAttribute.objects.create(product=self.product, name="Color")
        black = AttributeValue.objects.create(attribute=color_attr, value="Black")

        variant = ProductVariant.objects.create(product=self.product, sku="S24-BLK")
        VariantAttributeValue.objects.create(variant=variant, value=black)

        with self.assertRaises(Exception):
            VariantAttributeValue.objects.create(variant=variant, value=black)

    def test_attribute_value_unique_per_attribute(self):
        color_attr = ProductAttribute.objects.create(product=self.product, name="Color")
        AttributeValue.objects.create(attribute=color_attr, value="Black")

        with self.assertRaises(Exception):
            AttributeValue.objects.create(attribute=color_attr, value="Black")
