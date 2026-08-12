# catalog/serializers/media.py

from rest_framework import serializers

from catalog.models import ProductMedia


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = (
            "id",
            "media_type",
            "url",
            "thumbnail_url",
            "alt_text",
            "is_primary",
            "sort_order",
        )
