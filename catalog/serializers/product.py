# catalog/serializers/product.py

from rest_framework import serializers

from catalog.models import Product
from catalog.serializers.media import ProductMediaSerializer
from catalog.serializers.variant import ProductVariantSerializer


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "brand",
            "model",
            "category_name",
            "status",
            "is_active",
            "primary_image",
            "created_at",
        )

    def get_primary_image(self, obj: Product):
        media = obj.media.filter(is_primary=True, media_type="IMAGE").first()
        if media:
            return ProductMediaSerializer(media).data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True, read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)
    specifications = serializers.JSONField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "brand",
            "model",
            "description",
            "specifications",
            "status",
            "is_active",
            "category",
            "variants",
            "media",
            "created_at",
            "updated_at",
        )

    def get_category(self, obj: Product):
        return {
            "id": str(obj.category.id),
            "name": obj.category.name,
            "slug": obj.category.slug,
        }
