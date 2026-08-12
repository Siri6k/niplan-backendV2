# catalog/admin.py

from django.contrib import admin

from catalog.models import (
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductVariant,
    VariantAttributeValue,
)


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "sort_order")
    list_filter = ("product",)
    search_fields = ("name", "product__name")
    inlines = [AttributeValueInline]


class VariantAttributeValueInline(admin.TabularInline):
    model = VariantAttributeValue
    extra = 1


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "is_active", "created_at")
    list_filter = ("is_active", "product__category")
    search_fields = ("sku", "product__name")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [VariantAttributeValueInline]
    list_select_related = ("product",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "sort_order", "created_at")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "brand",
        "model",
        "category",
        "status",
        "is_active",
        "created_at",
    )
    list_filter = ("status", "is_active", "category", "brand")
    search_fields = ("name", "brand", "model", "slug", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)
    list_select_related = ("category",)
