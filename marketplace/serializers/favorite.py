from rest_framework import serializers

from marketplace.models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):

    listing_title = serializers.CharField(
        source="listing.title",
        read_only=True,
    )

    listing_price = serializers.DecimalField(
        source="listing.price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    listing_currency = serializers.CharField(
        source="listing.currency",
        read_only=True,
    )

    class Meta:
        model = Favorite

        fields = [
            "id",
            "listing",
            "listing_title",
            "listing_price",
            "listing_currency",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "listing_title",
            "listing_price",
            "listing_currency",
            "created_at",
        ]
