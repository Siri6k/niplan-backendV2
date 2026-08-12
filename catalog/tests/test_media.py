# catalog/tests/test_media.py

from django.test import TestCase

from catalog.models import (
    Category,
    Product,
    ProductMedia,
    ProductVariant,
)


class ProductMediaTests(TestCase):
    def setUp(self):
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
        )

    def test_create_product_media(self):
        media = ProductMedia.objects.create(
            product=self.product,
            media_type=ProductMedia.MediaType.IMAGE,
            url="https://example.com/s24.jpg",
            alt_text="Samsung Galaxy S24",
            is_primary=True,
        )

        self.assertEqual(media.product, self.product)
        self.assertTrue(media.is_primary)
        self.assertEqual(media.media_type, ProductMedia.MediaType.IMAGE)

    def test_product_can_have_multiple_media(self):
        ProductMedia.objects.create(
            product=self.product,
            url="https://example.com/s24-front.jpg",
            sort_order=0,
            is_primary=True,
        )

        ProductMedia.objects.create(
            product=self.product,
            url="https://example.com/s24-back.jpg",
            sort_order=1,
        )

        ProductMedia.objects.create(
            product=self.product,
            url="https://example.com/s24-side.jpg",
            sort_order=2,
        )

        self.assertEqual(self.product.media.count(), 3)

    def test_variant_can_have_media(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            sku="SAM-S24-BLK-256",
        )

        media = ProductMedia.objects.create(
            product=self.product,
            variant=variant,
            url="https://example.com/s24-black.jpg",
            is_primary=True,
        )

        self.assertEqual(media.variant, variant)
        self.assertEqual(variant.media.count(), 1)

    def test_media_ordering(self):
        ProductMedia.objects.create(
            product=self.product,
            url="https://example.com/s24-back.jpg",
            sort_order=2,
        )
        ProductMedia.objects.create(
            product=self.product,
            url="https://example.com/s24-front.jpg",
            sort_order=0,
            is_primary=True,
        )
        ProductMedia.objects.create(
            product=self.product,
            url="https://example.com/s24-side.jpg",
            sort_order=1,
        )

        media_list = list(self.product.media.all())
        self.assertEqual(media_list[0].url, "https://example.com/s24-front.jpg")
        self.assertEqual(media_list[1].url, "https://example.com/s24-side.jpg")
        self.assertEqual(media_list[2].url, "https://example.com/s24-back.jpg")

    def test_video_media(self):
        media = ProductMedia.objects.create(
            product=self.product,
            media_type=ProductMedia.MediaType.VIDEO,
            url="https://example.com/s24-video.mp4",
            thumbnail_url="https://example.com/s24-thumb.jpg",
        )

        self.assertEqual(media.media_type, ProductMedia.MediaType.VIDEO)
        self.assertEqual(media.thumbnail_url, "https://example.com/s24-thumb.jpg")
