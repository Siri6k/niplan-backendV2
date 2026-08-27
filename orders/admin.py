from decimal import Decimal

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        "listing",
        "seller",
        "quantity",
        "unit_price",
        "subtotal",
        "status",
        "created_at",
    )
    readonly_fields = (
        "listing",
        "seller",
        "quantity",
        "unit_price",
        "subtotal",
        "status",
        "created_at",
    )
    can_delete = False
    show_change_link = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "buyer",
        "seller",
        "status",
        "currency",
        "total",
        "item_count",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at", "updated_at")
    search_fields = ("id", "buyer__email", "seller__user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [OrderItemInline]
    fieldsets = (
        (
            "Informations générales",
            {"fields": ("id", "buyer", "seller", "status", "currency")},
        ),
        ("Totaux", {"fields": ("subtotal", "shipping_cost", "total")}),
        (
            "Dates",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = "Nb articles"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "listing",
        "seller",
        "quantity",
        "unit_price",
        "subtotal",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at", "seller")
    search_fields = ("order__id", "listing__title", "product_name", "sku")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "listing",
                    "seller",
                    "quantity",
                    "unit_price",
                    "subtotal",
                )
            },
        ),
        ("Détails produit", {"fields": ("product_name", "variant_name", "sku")}),
        ("Statut", {"fields": ("status",)}),
        (
            "Dates",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
