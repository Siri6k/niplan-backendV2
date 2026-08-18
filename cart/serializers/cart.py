# cart/serializers/cart.py

from rest_framework import serializers
from decimal import Decimal
from cart.models import Cart
from cart.serializers.cart_item import CartItemReadSerializer


class CartReadSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "status",
            "items",
            "item_count",
            "total",
            "currency",
            "created_at",
            "updated_at",
            "last_accessed_at",
        ]
        read_only_fields = fields

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total(self, obj):
        return sum(
            (item.listing.price * item.quantity for item in obj.items.all()),
            Decimal("0.00"),
        )

    def get_currency(self, obj):
        first_item = obj.items.select_related("listing").first()
        return first_item.listing.currency if first_item else None
