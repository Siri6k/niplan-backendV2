from rest_framework import serializers

from marketplace.models import Offer


class OfferCreateSerializer(serializers.Serializer):
    unit_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
    )

    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
    )

    message = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class OfferReadSerializer(serializers.ModelSerializer):
    total_amount = serializers.SerializerMethodField()
    listing_title = serializers.CharField(
        source="listing.title",
        read_only=True,
    )

    class Meta:
        model = Offer
        fields = [
            "id",
            "listing",
            "listing_title",
            "buyer",
            "unit_amount",
            "quantity",
            "total_amount",
            "currency",
            "message",
            "status",
            "parent_offer",
            "expires_at",
            "created_at",
            "updated_at",
            "responded_at",
        ]
        read_only_fields = fields

    def get_total_amount(self, obj):
        return obj.total_amount


class OfferActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            "accept",
            "reject",
            "counter",
            "cancel",
        ]
    )

    unit_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        required=False,
    )

    message = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate(self, data):
        if data.get("action") == "counter" and "unit_amount" not in data:
            raise serializers.ValidationError(
                {"unit_amount": "Requis pour une contre-offre."}
            )
        return data
