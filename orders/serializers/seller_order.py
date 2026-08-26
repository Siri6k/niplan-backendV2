from rest_framework import serializers

from orders.models import Order, OrderItem


class SellerOrderItemSerializer(serializers.ModelSerializer):
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
            "quantity",
            "unit_price",
            "subtotal",
        ]


class SellerOrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "currency",
            "subtotal",
            "total",
            "items",
            "created_at",
            "updated_at",
        ]

    def get_items(self, obj):
        # Le seller est extrait du contexte
        seller_user = self.context["request"].user
        items = obj.items.filter(listing__seller__user=seller_user).select_related(
            "listing",
            "listing__store",
            "listing__variant",
            "listing__variant__product",
        )
        return SellerOrderItemSerializer(items, many=True).data
