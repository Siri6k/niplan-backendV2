from django.core.exceptions import ValidationError
from django.db import transaction

from orders.models import Order, OrderItem


class OrderStatusService:
    # ---------------------------------------------------------
    # TRANSITIONS AUTORISÉES POUR UN ARTICLE
    # ---------------------------------------------------------
    ALLOWED_ITEM_TRANSITIONS = {
        OrderItem.Status.PENDING: {
            OrderItem.Status.PROCESSING,
            OrderItem.Status.CANCELLED,
        },
        OrderItem.Status.PROCESSING: {
            OrderItem.Status.SHIPPED,
            OrderItem.Status.CANCELLED,
        },
        OrderItem.Status.SHIPPED: {
            OrderItem.Status.DELIVERED,
        },
        OrderItem.Status.DELIVERED: set(),
        OrderItem.Status.CANCELLED: set(),
    }

    @staticmethod
    @transaction.atomic
    def update_item_status(*, seller_user, order_id, item_id, new_status):
        """
        Met à jour le statut d'une ligne de commande si elle appartient
        au vendeur connecté et si la transition est autorisée.
        """
        # Récupération de l'item avec verrouillage
        item = (
            OrderItem.objects.select_for_update()
            .select_related("order", "listing", "listing__seller")
            .filter(
                id=item_id,
                order_id=order_id,
                listing__seller__user=seller_user,
            )
            .first()
        )

        if item is None:
            raise ValidationError("Cette ligne de commande ne vous appartient pas.")

        if new_status not in OrderItem.Status.values:
            raise ValidationError("Statut de commande invalide.")

        current_status = item.status
        allowed = OrderStatusService.ALLOWED_ITEM_TRANSITIONS.get(current_status, set())

        if new_status not in allowed:
            raise ValidationError(
                f"Transition impossible : {current_status} → {new_status}."
            )

        # Mise à jour du statut
        item.status = new_status
        item.save(update_fields=["status", "updated_at"])

        # Synchronisation du statut global de la commande
        OrderStatusService._synchronize_order_status(order=item.order)

        return item

    @staticmethod
    def _synchronize_order_status(*, order):
        """
        Met à jour le statut de la commande en fonction
        des statuts de tous ses articles.
        """
        items_status = list(order.items.values_list("status", flat=True))

        if not items_status:
            return

        # Tous les articles sont annulés
        if all(s == OrderItem.Status.CANCELLED for s in items_status):
            order.status = Order.Status.CANCELLED

        # Tous les articles sont livrés
        elif all(s == OrderItem.Status.DELIVERED for s in items_status):
            order.status = Order.Status.DELIVERED

        # Au moins un article est expédié
        elif any(s == OrderItem.Status.SHIPPED for s in items_status):
            order.status = Order.Status.SHIPPED

        # Au moins un article est en préparation
        elif any(s == OrderItem.Status.PROCESSING for s in items_status):
            order.status = Order.Status.PROCESSING

        # Sinon, commande en attente
        else:
            order.status = Order.Status.PENDING

        order.save(update_fields=["status", "updated_at"])
