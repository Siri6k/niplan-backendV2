from rest_framework import serializers

from accounts.models import Store


class StoreSerializer(serializers.ModelSerializer):
    seller_email = serializers.EmailField(source="seller.user.email", read_only=True)

    class Meta:
        model = Store
        fields = (
            "id",
            "seller_email",
            "name",
            "slug",
            "description",
            "logo",
            "banner",
            "phone",
            "city",
            "address",
            "is_active",
            "is_open",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "seller_email",
            "is_open",
            "created_at",
            "updated_at",
        )


class StoreCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = (
            "name",
            "description",
            "logo",
            "banner",
            "phone",
            "city",
            "address",
            "is_active",
        )
