from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    """
    Autorise uniquement les utilisateurs ayant un SellerProfile.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "seller_profile")
        )


class IsStoreOwner(permissions.BasePermission):
    """
    Autorise uniquement le propriétaire de la boutique.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "seller_profile")
            and obj.seller == request.user.seller_profile
        )
