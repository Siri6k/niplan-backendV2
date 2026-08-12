# catalog/serializers/category.py

from rest_framework import serializers

from catalog.models import Category


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "sort_order",
            "children",
        )

    def get_children(self, obj: Category):
        if hasattr(obj, "children"):
            return CategorySerializer(
                obj.children.filter(is_active=True), many=True
            ).data
        return []


class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "sort_order",
            "children",
        )

    def get_children(self, obj: Category):
        if hasattr(obj, "children"):
            return CategoryTreeSerializer(
                obj.children.filter(is_active=True), many=True
            ).data
        return []
