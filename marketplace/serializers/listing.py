# marketplace/serializers/listing.py

from decimal import Decimal

from rest_framework import serializers

from accounts.models import Store
from catalog.models import ProductVariant
from marketplace.models import Listing


class ListingReadSerializer(serializers.ModelSerializer):
    """
    Serializer de lecture — enrichi avec les données du catalogue et du vendeur.
    """

    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    brand = serializers.CharField(source="variant.product.brand", read_only=True)
    variant_name = serializers.CharField(source="variant.display_title", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)
    seller_name = serializers.CharField(source="seller.user.full_name", read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "product_name",
            "brand",
            "variant_name",
            "sku",
            "store",
            "store_name",
            "seller_name",
            "price",
            "currency",
            "condition",
            "stock",
            "location",
            "is_negotiable",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ListingCreateSerializer(serializers.Serializer):
    """
    Serializer de création — le backend déduit le seller depuis request.user.
    Le client ne contrôle jamais : seller, status, published_at.
    """

    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
    )

    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)

    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3, default="USD")

    condition = serializers.ChoiceField(
        choices=Listing.Condition.choices,
        default=Listing.Condition.NEW,
    )
    stock = serializers.IntegerField(min_value=0, default=0)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_negotiable = serializers.BooleanField(default=False)

    def validate_price(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à zéro.")
        return value

    def validate_currency(self, value: str):
        value = value.upper()
        allowed = {"USD", "CDF", "ZAR", "ZMW"}
        if value not in allowed:
            raise serializers.ValidationError("Devise non supportée.")
        return value


class ListingUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=3, required=False)

    condition = serializers.ChoiceField(
        choices=Listing.Condition.choices, required=False
    )
    stock = serializers.IntegerField(min_value=0, required=False)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_negotiable = serializers.BooleanField(required=False)

    def validate_price(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à zéro.")
        return value

    def validate_currency(self, value: str):
        value = value.upper()
        allowed = {"USD", "CDF", "ZAR", "ZMW"}
        if value not in allowed:
            raise serializers.ValidationError("Devise non supportée.")
        return value


class ListingActionSerializer(serializers.Serializer):
    """
    Serializer pour les actions de workflow (publish, pause, archive).
    """

    action = serializers.ChoiceField(
        choices=[
            ("publish", "Publier"),
            ("pause", "Mettre en pause"),
            ("archive", "Archiver"),
        ]
    )
