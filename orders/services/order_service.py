from decimal import Decimal
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction

from cart.models import Cart
from cart.services.cart_service import CartService
from marketplace.models import Listing  # pour accéder au statut SOLD_OUT
from orders.models import Order, OrderItem


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_orders_from_cart(*, buyer):
        """
        Transforme le panier actif en commandes (une par vendeur).
        Verrouille les listings pour éviter les surventes.
        """
        # 1. Verrouiller le panier
        cart = (
            Cart.objects.select_for_update()
            .filter(buyer=buyer, status=Cart.Status.ACTIVE)
            .first()
        )
        if cart is None:
            raise ValidationError("Aucun panier actif.")

        # 2. Récupérer les items avec verrouillage
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

        # 3. Récupérer les listings avec verrouillage (pour revalidation)
        listing_ids = [item.listing_id for item in items]
        listings = {
            listing.id: listing
            for listing in Listing.objects.select_for_update().filter(
                id__in=listing_ids
            )
        }

        # 4. Valider le panier **après** verrouillage
        #    On réutilise la logique de CartService.validate_cart mais avec les listings verrouillés
        for item in items:
            listing = listings.get(item.listing_id)
            if listing is None:
                raise ValidationError(f"L'annonce {item.listing_id} n'existe plus.")
            if listing.status != Listing.Status.PUBLISHED:
                raise ValidationError(
                    f"L'article '{listing.title}' n'est plus disponible."
                )
            if listing.stock < item.quantity:
                raise ValidationError(
                    f"Stock insuffisant pour '{listing.title}'. "
                    f"Disponible : {listing.stock}, demandé : {item.quantity}."
                )
        # Vérification de la devise unique
        currencies = {listings[item.listing_id].currency for item in items}
        if len(currencies) > 1:
            raise ValidationError(
                "Toutes les annonces doivent utiliser la même devise."
            )
            # 5. Regrouper par vendeur
        items_by_seller = defaultdict(list)
        for cart_item in items:
            seller = cart_item.listing.seller
            items_by_seller[seller].append(cart_item)

        created_orders = []

        # 6. Créer une commande par vendeur
        for seller, seller_items in items_by_seller.items():
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
                listing = listings[cart_item.listing_id]

                unit_price = listing.price
                quantity = cart_item.quantity
                line_total = unit_price * quantity

                # Créer la ligne de commande
                OrderItem.objects.create(
                    order=order,
                    listing=listing,
                    seller=seller,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=line_total,
                    product_name=listing.variant.product.name,
                    variant_name=listing.variant.sku,
                    sku=listing.variant.sku,
                )

                subtotal += line_total

                # Décrémenter le stock
                listing.stock -= quantity

                # Passer en SOLD_OUT si le stock est épuisé
                if listing.stock == 0:
                    listing.status = Listing.Status.SOLD_OUT

                listing.save(update_fields=["stock", "status", "updated_at"])

            # Mise à jour des totaux de la commande
            order.subtotal = subtotal
            order.total = subtotal + order.shipping_cost
            order.save(update_fields=["subtotal", "total", "updated_at"])

            created_orders.append(order)

        # 7. Marquer le panier comme CHECKED_OUT
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
