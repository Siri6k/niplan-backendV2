# cart/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("listing", "quantity", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("listing",)
    verbose_name = _("Ligne du panier")
    verbose_name_plural = _("Lignes du panier")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "buyer",
        "status",
        "item_count",
        "total",
        "last_accessed_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("buyer__email", "buyer__first_name", "buyer__last_name", "id")
    readonly_fields = ("created_at", "updated_at", "last_accessed_at")
    inlines = [CartItemInline]

    fieldsets = (
        (None, {"fields": ("buyer", "status")}),
        (_("Dates"), {"fields": ("created_at", "updated_at", "last_accessed_at")}),
    )

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = _("Nombre d'articles")

    def total(self, obj):
        # Attention : suppose une seule devise par panier
        from decimal import Decimal

        return sum(
            (item.listing.price * item.quantity for item in obj.items.all()),
            Decimal("0.00"),
        )

    total.short_description = _("Total")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cart",
        "listing",
        "quantity",
        "subtotal",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("cart__buyer__email", "listing__title", "id")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("cart", "listing")

    fieldsets = (
        (None, {"fields": ("cart", "listing", "quantity")}),
        (_("Dates"), {"fields": ("created_at", "updated_at")}),
    )

    def subtotal(self, obj):
        return obj.listing.price * obj.quantity

    subtotal.short_description = _("Sous-total")
