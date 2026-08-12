# marketplace/admin.py

from django.contrib import admin

from marketplace.models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "store",
        "seller",
        "variant",
        "price",
        "currency",
        "condition",
        "stock",
        "status",
        "is_negotiable",
        "created_at",
    )
    list_filter = ("status", "condition", "currency", "is_negotiable", "created_at")
    search_fields = ("title", "description", "store__name", "variant__sku")
    readonly_fields = ("id", "created_at", "updated_at")
    list_select_related = ("seller", "store", "variant__product")
    ordering = ("-created_at",)
