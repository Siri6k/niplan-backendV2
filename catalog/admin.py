# catalog/admin.py

from django.contrib import admin

from catalog.models import (
    AttributeValue,
    Category,
    Product,
    ProductAttribute,
    ProductMedia,
    ProductVariant,
    VariantAttributeValue,
)


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1


class VariantAttributeValueInline(admin.TabularInline):
    model = VariantAttributeValue
    extra = 1


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "sort_order")
    list_filter = ("product",)
    search_fields = ("name", "product__name")
    inlines = [AttributeValueInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "is_active", "created_at")
    list_filter = ("is_active", "product__category")
    search_fields = ("sku", "product__name")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [VariantAttributeValueInline, ProductMediaInline]
    list_select_related = ("product",)


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "variant",
        "media_type",
        "is_primary",
        "sort_order",
        "created_at",
    )
    list_filter = ("media_type", "is_primary", "product__category")
    search_fields = ("product__name", "variant__sku", "alt_text")
    ordering = ("sort_order",)


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
    inlines = [ProductMediaInline]
