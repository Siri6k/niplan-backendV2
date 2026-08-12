# catalog/tests/test_category.py

from django.db.models.deletion import ProtectedError
from django.test import TestCase

from catalog.models import Category


class CategoryModelTests(TestCase):
    def test_create_root_category(self):
        category = Category.objects.create(
            name="Électronique",
            slug="electronique",
        )

        self.assertEqual(category.name, "Électronique")
        self.assertIsNone(category.parent)
        self.assertTrue(category.is_active)
        self.assertEqual(category.depth, 0)
        self.assertTrue(category.is_root)

    def test_create_child_category(self):
        parent = Category.objects.create(
            name="Électronique",
            slug="electronique",
        )

        child = Category.objects.create(
            name="Téléphones",
            slug="telephones",
            parent=parent,
        )

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())
        self.assertEqual(child.depth, 1)
        self.assertFalse(child.is_root)

    def test_create_nested_category(self):
        electronics = Category.objects.create(
            name="Électronique",
            slug="electronique",
        )

        phones = Category.objects.create(
            name="Téléphones",
            slug="telephones",
            parent=electronics,
        )

        smartphones = Category.objects.create(
            name="Smartphones",
            slug="smartphones",
            parent=phones,
        )

        self.assertEqual(smartphones.parent, phones)
        self.assertEqual(phones.parent, electronics)
        self.assertEqual(smartphones.depth, 2)
        self.assertEqual(
            smartphones.full_path, "Électronique > Téléphones > Smartphones"
        )

    def test_slug_must_be_unique(self):
        Category.objects.create(
            name="Téléphones",
            slug="telephones",
        )

        with self.assertRaises(Exception):
            Category.objects.create(
                name="Phones",
                slug="telephones",
            )

    def test_parent_category_is_protected(self):
        parent = Category.objects.create(
            name="Électronique",
            slug="electronique",
        )

        Category.objects.create(
            name="Téléphones",
            slug="telephones",
            parent=parent,
        )

        with self.assertRaises(ProtectedError):
            parent.delete()

    def test_category_sort_order(self):
        Category.objects.create(name="Zebra", slug="zebra", sort_order=10)
        Category.objects.create(name="Apple", slug="apple", sort_order=0)

        categories = list(Category.objects.all())
        self.assertEqual(categories[0].name, "Apple")
        self.assertEqual(categories[1].name, "Zebra")
