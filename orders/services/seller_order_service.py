from django.core.exceptions import ValidationError
from orders.models import Order, OrderItem


class SellerOrderService:

    @staticmethod
    def get_seller_orders(*, seller_user):
        """
        Retourne les commandes contenant au moins un article
        appartenant au vendeur.
        """
        return (
            Order.objects.filter(items__listing__seller__user=seller_user)
            .distinct()
            .prefetch_related(
                "items",
                "items__listing",
                "items__listing__store",
                "items__listing__variant",
                "items__listing__variant__product",
            )
            .order_by("-created_at")
        )

    @staticmethod
    def get_seller_order(*, seller_user, order_id):
        """
        Retourne une commande si elle contient au moins un article
        du vendeur.
        """
        return (
            Order.objects.filter(id=order_id, items__listing__seller__user=seller_user)
            .distinct()
            .prefetch_related(
                "items",
                "items__listing",
                "items__listing__store",
                "items__listing__variant",
                "items__listing__variant__product",
            )
            .first()
        )

    @staticmethod
    def get_seller_order_item(*, seller_user, order_id, item_id):
        """
        Retourne une ligne de commande si elle appartient au vendeur.
        """
        item = (
            OrderItem.objects.select_related("order", "listing", "listing__seller")
            .filter(
                id=item_id,
                order_id=order_id,
                listing__seller__user=seller_user,
            )
            .first()
        )
        if item is None:
            raise ValidationError("Cette ligne de commande ne vous appartient pas.")
        return item
