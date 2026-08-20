from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from cart.models import Cart, CartItem
from marketplace.models import Listing


class CartService:
    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------
    @staticmethod
    def _touch_cart(cart):
        """Met à jour la date de dernière activité du panier."""
        cart.last_accessed_at = timezone.now()
        cart.save(update_fields=["last_accessed_at", "updated_at"])

    # ---------------------------------------------------------
    # GET OR CREATE ACTIVE CART
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def get_or_create_active_cart(*, buyer):
        """
        Retourne le panier actif du buyer.
        Garantit qu'un seul panier ACTIVE existe par utilisateur.
        """
        cart = (
            Cart.objects.select_for_update()
            .filter(
                buyer=buyer,
                status=Cart.Status.ACTIVE,
            )
            .first()
        )

        if cart:
            CartService._touch_cart(cart)
            return cart

        # Le UniqueConstraint protège la création concurrente.
        # On utilise un savepoint afin de pouvoir récupérer proprement
        # le panier créé par une requête concurrente.
        try:
            with transaction.atomic():
                cart = Cart.objects.create(
                    buyer=buyer,
                    status=Cart.Status.ACTIVE,
                )
        except IntegrityError:
            cart = Cart.objects.select_for_update().get(
                buyer=buyer,
                status=Cart.Status.ACTIVE,
            )

        CartService._touch_cart(cart)
        return cart

    @staticmethod
    def get_active_cart_with_items(*, buyer):
        """
        Retourne le panier actif avec ses articles.
        """
        cart = (
            Cart.objects.filter(
                buyer=buyer,
                status=Cart.Status.ACTIVE,
            )
            .prefetch_related(
                "items",
                "items__listing",
                "items__listing__store",
                "items__listing__variant",
                "items__listing__variant__product",
            )
            .first()
        )

        if cart:
            CartService._touch_cart(cart)

        return cart

    # ---------------------------------------------------------
    # LISTING VALIDATION
    # ---------------------------------------------------------
    @staticmethod
    def validate_listing(*, listing, quantity, cart=None):
        if listing.status != Listing.Status.PUBLISHED:
            raise ValidationError("Cette annonce n'est pas disponible à l'achat.")

        if listing.stock <= 0:
            raise ValidationError("Cette annonce est épuisée.")

        if quantity <= 0:
            raise ValidationError("La quantité doit être supérieure à zéro.")

        if quantity > listing.stock:
            raise ValidationError("La quantité demandée dépasse le stock disponible.")

        if cart is not None:
            if listing.seller.user_id == cart.buyer_id:
                raise ValidationError(
                    "Vous ne pouvez pas ajouter votre propre annonce au panier."
                )

            existing_items = cart.items.select_related("listing").all()

            currencies = {
                item.listing.currency for item in existing_items if item.listing
            }

            if currencies:
                currencies.add(listing.currency)

                if len(currencies) > 1:
                    raise ValidationError(
                        "Tous les articles d'un panier doivent avoir la même devise."
                    )

    # ---------------------------------------------------------
    # ADD ITEM
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def add_item(*, buyer, listing, quantity):
        """
        Ajoute un listing au panier.

        Si le listing existe déjà dans le panier,
        sa quantité est augmentée.
        """

        cart = CartService.get_or_create_active_cart(buyer=buyer)

        CartService.validate_listing(
            listing=listing,
            quantity=quantity,
            cart=cart,
        )

        item = (
            CartItem.objects.select_for_update()
            .filter(
                cart=cart,
                listing=listing,
            )
            .first()
        )

        created = False

        if item:
            new_quantity = item.quantity + quantity

            if new_quantity > listing.stock:
                raise ValidationError(
                    "La quantité totale demandée dépasse " "le stock disponible."
                )

            item.quantity = new_quantity

            item.save(
                update_fields=[
                    "quantity",
                    "updated_at",
                ]
            )

        else:
            item = CartItem.objects.create(
                cart=cart,
                listing=listing,
                quantity=quantity,
            )
            created = True

        CartService._touch_cart(cart)

        return item, created

    # ---------------------------------------------------------
    # UPDATE QUANTITY
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def update_item_quantity(*, buyer, item, quantity):
        """
        Modifie la quantité d'un article du panier.
        """

        cart = item.cart

        if cart.buyer_id != buyer.id:
            raise ValidationError("Vous ne pouvez pas modifier cet article.")

        if cart.status != Cart.Status.ACTIVE:
            raise ValidationError("Ce panier n'est plus actif.")

        CartService.validate_listing(
            listing=item.listing,
            quantity=quantity,
        )

        item.quantity = quantity

        item.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        CartService._touch_cart(cart)

        return item

    # ---------------------------------------------------------
    # REMOVE ITEM
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def remove_item(*, buyer, item):
        if item.cart.buyer_id != buyer.id:
            raise ValidationError("Vous ne pouvez pas supprimer cet article.")

        if item.cart.status != Cart.Status.ACTIVE:
            raise ValidationError("Ce panier n'est plus actif.")

        cart = item.cart

        item.delete()

        CartService._touch_cart(cart)

    # ---------------------------------------------------------
    # CLEAR CART
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def clear_cart(*, buyer):
        """
        Vide le panier actif.
        Le panier lui-même reste ACTIVE.
        """

        cart = CartService.get_or_create_active_cart(buyer=buyer)

        cart.items.all().delete()

        CartService._touch_cart(cart)

        return cart

    # ---------------------------------------------------------
    # TOTAL
    # ---------------------------------------------------------
    @staticmethod
    def get_cart_total(*, cart):
        """
        Calcule le total courant du panier.
        """

        total = Decimal("0.00")

        items = cart.items.select_related("listing")

        for item in items:
            total += item.listing.price * item.quantity

        return total

    # ---------------------------------------------------------
    # CART VALIDATION
    # ---------------------------------------------------------
    @staticmethod
    def validate_cart(*, cart):
        """
        Vérifie que le panier peut être envoyé au checkout.
        """

        if cart.status != Cart.Status.ACTIVE:
            raise ValidationError("Ce panier n'est plus actif.")

        items = list(cart.items.select_related("listing"))

        if not items:
            raise ValidationError("Votre panier est vide.")

        currencies = set()
        errors = []

        for item in items:
            listing = item.listing

            if listing.status != Listing.Status.PUBLISHED:
                errors.append(f"Le listing {listing.id} n'est plus disponible.")
                continue

            if listing.stock <= 0:
                errors.append(f"Le listing {listing.id} est épuisé.")
                continue

            if item.quantity > listing.stock:
                errors.append(
                    f"Stock insuffisant pour le listing {listing.id}. "
                    f"Disponible : {listing.stock}, "
                    f"demandé : {item.quantity}."
                )

            currencies.add(listing.currency)

        if len(currencies) > 1:
            errors.append(
                "Tous les articles d'un panier doivent avoir " "la même devise."
            )

        if errors:
            raise ValidationError(errors)

        return True

    # ---------------------------------------------------------
    # CLEAN INVALID ITEMS
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def clean_cart(*, cart):
        """
        Nettoie les articles qui ne sont plus achetables.

        Si le stock a diminué mais reste supérieur à zéro,
        la quantité du panier est ajustée au stock disponible.

        Les articles dont le listing n'est plus publiable
        sont supprimés.
        """

        items = list(cart.items.select_related("listing"))

        for item in items:
            listing = item.listing

            if listing.status != Listing.Status.PUBLISHED:
                item.delete()
                continue

            if listing.stock <= 0:
                item.delete()
                continue

            if item.quantity > listing.stock:
                item.quantity = listing.stock

                item.save(
                    update_fields=[
                        "quantity",
                        "updated_at",
                    ]
                )

        return cart

    # ---------------------------------------------------------
    # MARK ABANDONED
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def mark_abandoned(*, cart):
        """
        Marque un panier actif comme abandonné.
        """

        if cart.status == Cart.Status.ACTIVE:
            cart.status = Cart.Status.ABANDONED

            cart.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return cart
