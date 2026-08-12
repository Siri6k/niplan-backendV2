from rest_framework import serializers

from accounts.models import SellerProfile


class SellerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = SellerProfile
        fields = (
            "id",
            "email",
            "full_name",
            "seller_type",
            "verification_status",
            "rating",
            "total_sales",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "email",
            "full_name",
            "verification_status",
            "rating",
            "total_sales",
            "created_at",
            "updated_at",
        )


class BecomeSellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ("seller_type",)

    def validate(self, attrs):
        user = self.context["request"].user
        if hasattr(user, "seller_profile"):
            raise serializers.ValidationError(
                {"detail": "Vous êtes déjà vendeur."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)