# cart/services/cart_service.py

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from cart.models import Cart, CartItem
from marketplace.models import Listing


class CartService:
    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------
    @staticmethod
    def _touch_cart(cart):
        """Met à jour la date de dernier accès du panier."""
        cart.last_accessed_at = timezone.now()
        cart.save(update_fields=["last_accessed_at", "updated_at"])

    # ---------------------------------------------------------
    # GET OR CREATE ACTIVE CART
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def get_or_create_active_cart(*, buyer):
        cart = (
            Cart.objects.select_for_update()
            .filter(buyer=buyer, status=Cart.Status.ACTIVE)
            .first()
        )
        if cart:
            CartService._touch_cart(cart)
            return cart
        cart = Cart.objects.create(buyer=buyer, status=Cart.Status.ACTIVE)
        CartService._touch_cart(cart)
        return cart

    @staticmethod
    def get_active_cart_with_items(*, buyer):
        cart = (
            Cart.objects.filter(buyer=buyer, status=Cart.Status.ACTIVE)
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
        cart = CartService.get_or_create_active_cart(buyer=buyer)
        CartService.validate_listing(listing=listing, quantity=quantity, cart=cart)
        item = (
            CartItem.objects.select_for_update()
            .filter(cart=cart, listing=listing)
            .first()
        )
        if item:
            new_quantity = item.quantity + quantity
            if new_quantity > listing.stock:
                raise ValidationError(
                    "La quantité totale demandée dépasse le stock disponible."
                )
            item.quantity = new_quantity
            item.save(update_fields=["quantity", "updated_at"])
        else:
            item = CartItem.objects.create(
                cart=cart, listing=listing, quantity=quantity
            )
        # Nettoyage éventuel des articles invalides (statut, stock)
        CartService.clean_cart(cart=cart)
        CartService._touch_cart(cart)
        return item

    # ---------------------------------------------------------
    # UPDATE QUANTITY
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def update_item_quantity(*, buyer, item, quantity):
        if item.cart.buyer_id != buyer.id:
            raise ValidationError("Vous ne pouvez pas modifier cet article.")
        if item.cart.status != Cart.Status.ACTIVE:
            raise ValidationError("Ce panier n'est plus actif.")
        CartService.validate_listing(listing=item.listing, quantity=quantity)
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        CartService.clean_cart(cart=item.cart)
        CartService._touch_cart(item.cart)
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
        item.delete()
        CartService._touch_cart(item.cart)

    # ---------------------------------------------------------
    # CLEAR CART
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def clear_cart(*, buyer):
        cart = CartService.get_or_create_active_cart(buyer=buyer)
        cart.items.all().delete()
        CartService._touch_cart(cart)
        return cart

    # ---------------------------------------------------------
    # TOTAL
    # ---------------------------------------------------------
    @staticmethod
    def get_cart_total(*, cart):
        total = Decimal("0.00")
        for item in cart.items.select_related("listing").all():
            total += item.listing.price * item.quantity
        return total

    # ---------------------------------------------------------
    # CART VALIDATION
    # ---------------------------------------------------------
    @staticmethod
    def validate_cart(*, cart):
        if cart.status != Cart.Status.ACTIVE:
            raise ValidationError("Ce panier n'est plus actif.")
        items = cart.items.select_related("listing").all()
        if not items.exists():
            raise ValidationError("Votre panier est vide.")
        errors = []
        for item in items:
            listing = item.listing
            if listing.status != Listing.Status.PUBLISHED:
                errors.append(f"Le listing {listing.id} n'est plus disponible.")
                continue
            if listing.stock < item.quantity:
                errors.append(f"Stock insuffisant pour le listing {listing.id}.")
        if errors:
            raise ValidationError(errors)
        return True

    # ---------------------------------------------------------
    # CLEAN INVALID ITEMS
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def clean_cart(*, cart):
        items = cart.items.select_related("listing").all()
        for item in items:
            listing = item.listing
            if listing.status != Listing.Status.PUBLISHED or listing.stock <= 0:
                item.delete()
            elif listing.stock < item.quantity:
                item.delete()
        return cart

    # ---------------------------------------------------------
    # MARK ABANDONED
    # ---------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def mark_abandoned(*, cart):
        if cart.status == Cart.Status.ACTIVE:
            cart.status = Cart.Status.ABANDONED
            cart.save(update_fields=["status", "updated_at"])
        return cart
