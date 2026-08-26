from rest_framework import serializers

from orders.models import Order, OrderItem


class OrderItemReadSerializer(serializers.ModelSerializer):
    # Dénormalisation pour le frontend
    product_name = serializers.CharField(
        source="listing.variant.product.name",
        read_only=True,
    )
    brand = serializers.CharField(
        source="listing.variant.product.brand",
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
    store_name = serializers.CharField(
        source="listing.store.name",
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "listing",
            "listing_title",
            "product_name",
            "brand",
            "sku",
            "store_name",
            "seller",  # ID du vendeur
            "quantity",
            "unit_price",
            "subtotal",
        ]


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "currency",
            "subtotal",
            "shipping_cost",
            "total",
            "item_count",
            "items",
            "created_at",
            "updated_at",
        ]

    def get_item_count(self, obj):
        return obj.items.count()
