# marketplace/admin.py
from django.contrib import admin

from marketplace.models import Favorite, Listing, Offer


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


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "listing",
        "created_at",
    ]

    list_filter = [
        "created_at",
    ]

    search_fields = [
        "user__email",
        "listing__title",
    ]

    raw_id_fields = [
        "user",
        "listing",
    ]


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "listing",
        "buyer",
        "unit_amount",
        "quantity",
        "total_amount",
        "currency",
        "status",
        "parent_offer",
        "created_at",
        "responded_at",
    ]

    list_filter = [
        "status",
        "currency",
        "created_at",
        "responded_at",
    ]

    search_fields = [
        "listing__title",
        "buyer__email",
        "message",
    ]

    readonly_fields = [
        "id",
        "total_amount",
        "created_at",
        "updated_at",
        "responded_at",
    ]

    raw_id_fields = [
        "listing",
        "buyer",
        "parent_offer",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "listing",
                    "buyer",
                    "parent_offer",
                )
            },
        ),
        (
            "Détails de l'offre",
            {
                "fields": (
                    "unit_amount",
                    "quantity",
                    "total_amount",
                    "currency",
                    "message",
                )
            },
        ),
        (
            "Statut",
            {
                "fields": (
                    "status",
                    "expires_at",
                )
            },
        ),
        (
            "Horodatage",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "responded_at",
                )
            },
        ),
    )

    def total_amount(self, obj):
        return obj.total_amount

    total_amount.short_description = "Montant total"
