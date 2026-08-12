# catalog/serializers/variant.py

from rest_framework import serializers

from catalog.models import ProductVariant
from catalog.serializers.media import ProductMediaSerializer


class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_summary = serializers.CharField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ("id", "sku", "is_active", "attribute_summary", "created_at")


class VariantDetailSerializer(serializers.ModelSerializer):
    attribute_summary = serializers.CharField(read_only=True)
    display_title = serializers.CharField(read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)
    values = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "is_active",
            "attribute_summary",
            "display_title",
            "media",
            "values",
            "created_at",
        )

    def get_values(self, obj: ProductVariant):
        return [
            {
                "attribute": v.value.attribute.name,
                "value": v.value.value,
            }
            for v in obj.variant_values.select_related("value__attribute").all()
        ]
