# cart/serializers/cart_item.py

from rest_framework import serializers

from cart.models import CartItem


class CartItemReadSerializer(serializers.ModelSerializer):
    """Sérialiseur de lecture d'un article du panier."""

    product_name = serializers.CharField(
        source="listing.variant.product.name",
        read_only=True,
    )
    brand = serializers.CharField(
        source="listing.variant.product.brand",
        read_only=True,
    )
    variant_name = serializers.CharField(
        source="listing.variant.display_title",
        read_only=True,
    )
    sku = serializers.CharField(
        source="listing.variant.sku",
        read_only=True,
    )
    listing_title = serializers.CharField(
        source="listing.title",
        read_only=True,
    )
    seller_name = serializers.CharField(
        source="listing.store.name",
        read_only=True,
    )
    unit_price = serializers.DecimalField(
        source="listing.price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    currency = serializers.CharField(
        source="listing.currency",
        read_only=True,
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "listing",
            "listing_title",
            "product_name",
            "brand",
            "variant_name",
            "sku",
            "seller_name",
            "unit_price",
            "currency",
            "quantity",
            "subtotal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_subtotal(self, obj):
        return obj.listing.price * obj.quantity


class CartItemCreateSerializer(serializers.Serializer):
    """Sérialiseur utilisé pour ajouter un listing au panier."""

    listing = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class CartItemUpdateSerializer(serializers.Serializer):
    """Sérialiseur utilisé pour modifier la quantité d'un article."""

    quantity = serializers.IntegerField(min_value=1)
