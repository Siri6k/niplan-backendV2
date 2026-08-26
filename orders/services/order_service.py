from decimal import Decimal
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction

from cart.models import Cart
from cart.services.cart_service import CartService
from orders.models import Order, OrderItem


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_orders_from_cart(*, buyer):
        """
        Transforme le panier actif en une ou plusieurs commandes,
        une par vendeur.

        Retourne la liste des commandes créées.
        """
        cart = (
            Cart.objects.select_for_update()
            .prefetch_related(
                "items",
                "items__listing",
                "items__listing__store",
                "items__listing__variant",
                "items__listing__variant__product",
            )
            .filter(buyer=buyer, status=Cart.Status.ACTIVE)
            .first()
        )

        if cart is None:
            raise ValidationError("Aucun panier actif.")

        # Validation complète du panier (stock, disponibilité, devise, etc.)
        CartService.validate_cart(cart=cart)

        items = list(
            cart.items.select_for_update().select_related(
                "listing",
                "listing__seller",
                "listing__store",
                "listing__variant",
                "listing__variant__product",
            )
        )

        if not items:
            raise ValidationError("Votre panier est vide.")

        # -----------------------------------------------------
        # Regrouper les articles par vendeur
        # -----------------------------------------------------
        items_by_seller = defaultdict(list)
        for cart_item in items:
            seller = cart_item.listing.seller
            items_by_seller[seller].append(cart_item)

        created_orders = []

        # -----------------------------------------------------
        # Créer une commande par vendeur
        # -----------------------------------------------------
        for seller, seller_items in items_by_seller.items():
            # Devise commune (vérifiée par validate_cart)
            currency = seller_items[0].listing.currency

            order = Order.objects.create(
                buyer=buyer,
                seller=seller,
                status=Order.Status.PENDING,
                currency=currency,
                subtotal=Decimal("0.00"),
                shipping_cost=Decimal("0.00"),
                total=Decimal("0.00"),
            )

            subtotal = Decimal("0.00")

            for cart_item in seller_items:
                listing = cart_item.listing

                # Revalidation du stock (peut avoir changé entre temps)
                if listing.stock < cart_item.quantity:
                    raise ValidationError(f"Stock insuffisant pour : {listing.title}.")

                if listing.status != listing.Status.PUBLISHED:
                    raise ValidationError(
                        f"L'article {listing.title} n'est plus disponible."
                    )

                unit_price = listing.price
                quantity = cart_item.quantity
                line_total = unit_price * quantity

                OrderItem.objects.create(
                    order=order,
                    listing=listing,
                    seller=seller,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=line_total,
                    product_name=listing.variant.product.name,
                    variant_name=listing.variant.sku,  # ou un champ dédié
                    sku=listing.variant.sku,
                )

                subtotal += line_total

                # Diminution du stock
                listing.stock -= quantity
                listing.save(update_fields=["stock", "updated_at"])

            # Mise à jour des totaux de la commande
            order.subtotal = subtotal
            order.total = subtotal + order.shipping_cost
            order.save(update_fields=["subtotal", "total", "updated_at"])

            created_orders.append(order)

        # -----------------------------------------------------
        # Marquer le panier comme terminé
        # -----------------------------------------------------
        cart.status = Cart.Status.CHECKED_OUT
        cart.save(update_fields=["status", "updated_at"])

        return created_orders

    @staticmethod
    def get_order(*, buyer, order_id):
        """Retourne une commande si elle appartient à l'acheteur."""
        return (
            Order.objects.prefetch_related(
                "items", "items__listing", "items__listing__store"
            )
            .filter(id=order_id, buyer=buyer)
            .first()
        )

    @staticmethod
    @transaction.atomic
    def cancel_order(*, buyer, order_id):
        """
        Annule une commande PENDING ou CONFIRMED et restitue le stock.
        """
        order = (
            Order.objects.select_for_update()
            .prefetch_related("items", "items__listing")
            .filter(id=order_id, buyer=buyer)
            .first()
        )

        if order is None:
            raise ValidationError("Commande introuvable.")

        if order.status not in [Order.Status.PENDING, Order.Status.CONFIRMED]:
            raise ValidationError("Cette commande ne peut plus être annulée.")

        for item in order.items.all():
            listing = item.listing
            listing.stock += item.quantity
            listing.save(update_fields=["stock", "updated_at"])

        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])

        return order

    @staticmethod
    @transaction.atomic
    def update_status(*, order, new_status):
        """Change le statut d'une commande selon une machine d'états."""
        allowed_transitions = {
            Order.Status.PENDING: {
                Order.Status.CONFIRMED,
                Order.Status.CANCELLED,
            },
            Order.Status.CONFIRMED: {
                Order.Status.PROCESSING,
                Order.Status.CANCELLED,
            },
            Order.Status.PROCESSING: {
                Order.Status.SHIPPED,
            },
            Order.Status.SHIPPED: {
                Order.Status.DELIVERED,
            },
            Order.Status.DELIVERED: set(),
            Order.Status.CANCELLED: set(),
        }

        if new_status not in Order.Status.values:
            raise ValidationError("Statut invalide.")

        if new_status not in allowed_transitions.get(order.status, set()):
            raise ValidationError(
                f"Transition impossible : {order.status} → {new_status}."
            )

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        return order
