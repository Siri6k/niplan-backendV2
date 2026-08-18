# cart/serializers/cart.py

from decimal import Decimal

from rest_framework import serializers

from cart.models import Cart
from cart.serializers.cart_item import CartItemReadSerializer


class CartReadSerializer(serializers.ModelSerializer):
    """Sérialiseur de lecture du panier complet."""

    items = CartItemReadSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "status",
            "items",
            "item_count",
            "total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total(self, obj):
        # Attention : ce calcul suppose une devise unique par panier.
        # Pour le MVP, nous acceptons une seule devise ; dans une version
        # évoluée, il faudra gérer les devises multiples.
        return sum(
            (item.listing.price * item.quantity for item in obj.items.all()),
            Decimal("0.00"),
        )
