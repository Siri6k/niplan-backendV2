# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Profile, SellerProfile, Store, User


# ------------------------------------------------------------------------------
# User admin
# ------------------------------------------------------------------------------
class UserAdmin(BaseUserAdmin):
    """
    Administration du modèle User custom (email comme identifiant).
    """

    ordering = ["-date_joined"]
    list_display = [
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "is_active",
        "is_staff",
        "is_seller",
        "date_joined",
    ]
    list_filter = [
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    ]
    search_fields = [
        "email",
        "first_name",
        "last_name",
        "phone_number",
    ]
    readonly_fields = ["last_login", "date_joined"]
    filter_horizontal = [
        "groups",
        "user_permissions",
    ]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Informations personnelles"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    def is_seller(self, obj):
        """Affiche si l'utilisateur possède un profil vendeur."""
        return obj.is_seller

    is_seller.boolean = True
    is_seller.short_description = _("Vendeur")


# ------------------------------------------------------------------------------
# Profile admin
# ------------------------------------------------------------------------------
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "city",
        "country",
        "preferred_currency",
        "language",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "country",
        "city",
        "preferred_currency",
        "language",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "city",
        "country",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("user",)}),
        (_("Média"), {"fields": ("avatar",)}),
        (_("Bio"), {"fields": ("bio",)}),
        (_("Localisation"), {"fields": ("city", "country")}),
        (_("Préférences"), {"fields": ("preferred_currency", "language")}),
        (_("Métadonnées"), {"fields": ("created_at", "updated_at")}),
    )


# ------------------------------------------------------------------------------
# SellerProfile admin
# ------------------------------------------------------------------------------
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "seller_type",
        "verification_status",
        "rating",
        "total_sales",
        "is_verified",
        "can_sell",
        "created_at",
    ]
    list_filter = [
        "seller_type",
        "verification_status",
        "created_at",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
    ]
    readonly_fields = [
        "rating",
        "total_sales",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (None, {"fields": ("user",)}),
        (
            _("Type & statut"),
            {
                "fields": (
                    "seller_type",
                    "verification_status",
                )
            },
        ),
        (
            _("Données dérivées"),
            {
                "fields": (
                    "rating",
                    "total_sales",
                ),
                "description": _(
                    "Ces champs sont calculés automatiquement et ne doivent pas être modifiés manuellement."
                ),
            },
        ),
        (_("Métadonnées"), {"fields": ("created_at", "updated_at")}),
    )

    def is_verified(self, obj):
        return obj.is_verified

    is_verified.boolean = True
    is_verified.short_description = _("Vérifié")

    def can_sell(self, obj):
        return obj.can_sell

    can_sell.boolean = True
    can_sell.short_description = _("Peut vendre")


# ------------------------------------------------------------------------------
# Store admin
# ------------------------------------------------------------------------------
class StoreAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "seller",
        "city",
        "phone",
        "is_active",
        "is_open",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "city",
        "created_at",
    ]
    search_fields = [
        "name",
        "slug",
        "seller__user__email",
        "seller__user__first_name",
        "seller__user__last_name",
        "city",
    ]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("seller",)}),
        (
            _("Identité visuelle"),
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                )
            },
        ),
        (_("Média"), {"fields": ("logo", "banner")}),
        (
            _("Contact & localisation"),
            {
                "fields": (
                    "phone",
                    "city",
                    "address",
                )
            },
        ),
        (_("Statut"), {"fields": ("is_active",)}),
        (_("Métadonnées"), {"fields": ("created_at", "updated_at")}),
    )

    def is_open(self, obj):
        return obj.is_open

    is_open.boolean = True
    is_open.short_description = _("Ouverte")


# ------------------------------------------------------------------------------
# Inlines (optionnels)
# ------------------------------------------------------------------------------
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = _("Profil")


class SellerProfileInline(admin.StackedInline):
    model = SellerProfile
    can_delete = False
    verbose_name_plural = _("Profil vendeur")


class StoreInline(admin.StackedInline):
    model = Store
    can_delete = False
    verbose_name_plural = _("Boutique")


# Ajout des inlines dans l'admin User
UserAdmin.inlines = [ProfileInline, SellerProfileInline]
SellerProfileAdmin.inlines = [StoreInline]


# ------------------------------------------------------------------------------
# Enregistrement
# ------------------------------------------------------------------------------
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(SellerProfile, SellerProfileAdmin)
admin.site.register(Store, StoreAdmin)
