# cart/services/cart_service.py

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from cart.models import Cart, CartItem
from marketplace.models import Listing


class CartService:
    """
    Logique métier du panier.
    Le Cart manipule des Listings, jamais directement des Products ou ProductVariants.
    """

    # ---------------------------------------------------------
    # CART
    # ---------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def get_or_create_active_cart(*, buyer):
        """
        Retourne le panier actif du buyer (avec verrouillage).
        Le crée s'il n'en possède pas.
        """
        cart = (
            Cart.objects.select_for_update()
            .filter(buyer=buyer, status=Cart.Status.ACTIVE)
            .first()
        )
        if cart:
            return cart
        return Cart.objects.create(buyer=buyer, status=Cart.Status.ACTIVE)

    @staticmethod
    def get_active_cart_with_items(*, buyer):
        """
        Retourne le panier actif avec ses items préchargés pour les lectures.
        Ne crée pas de panier si inexistant.
        """
        return (
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

    # ---------------------------------------------------------
    # LISTING VALIDATION
    # ---------------------------------------------------------

    @staticmethod
    def validate_listing(*, listing, quantity, cart=None):
        """
        Vérifie qu'un Listing peut être ajouté au panier.
        Si `cart` est fourni, vérifie aussi la cohérence des devises.
        """
        if listing.status != Listing.Status.PUBLISHED:
            raise ValidationError("Cette annonce n'est pas disponible à l'achat.")

        if listing.stock <= 0:
            raise ValidationError("Cette annonce est épuisée.")

        if quantity <= 0:
            raise ValidationError("La quantité doit être supérieure à zéro.")

        if quantity > listing.stock:
            raise ValidationError("La quantité demandée dépasse le stock disponible.")

        if cart is not None:
            # Vérifier que toutes les devises correspondent
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
        Ajoute un Listing au panier.
        Si le Listing existe déjà, augmente la quantité.
        """
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
            return item

        return CartItem.objects.create(
            cart=cart,
            listing=listing,
            quantity=quantity,
        )

    # ---------------------------------------------------------
    # UPDATE QUANTITY
    # ---------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def update_item_quantity(*, buyer, item, quantity):
        """
        Modifie la quantité d'un CartItem.
        """
        if item.cart.buyer_id != buyer.id:
            raise ValidationError("Vous ne pouvez pas modifier cet article.")

        if item.cart.status != Cart.Status.ACTIVE:
            raise ValidationError("Ce panier n'est plus actif.")

        # On ne passe pas le cart à validate_listing car la devise ne change pas
        CartService.validate_listing(listing=item.listing, quantity=quantity)

        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        return item

    # ---------------------------------------------------------
    # REMOVE ITEM
    # ---------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def remove_item(*, buyer, item):
        """
        Supprime un article du panier.
        """
        if item.cart.buyer_id != buyer.id:
            raise ValidationError("Vous ne pouvez pas supprimer cet article.")
        if item.cart.status != Cart.Status.ACTIVE:
            raise ValidationError("Ce panier n'est plus actif.")
        item.delete()

    # ---------------------------------------------------------
    # CLEAR CART
    # ---------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def clear_cart(*, buyer):
        """
        Vide complètement le panier actif.
        """
        cart = CartService.get_or_create_active_cart(buyer=buyer)
        cart.items.all().delete()
        return cart

    # ---------------------------------------------------------
    # TOTAL
    # ---------------------------------------------------------

    @staticmethod
    def get_cart_total(*, cart):
        """
        Calcule le total courant du panier.
        Suppose qu'un panier n'a qu'une seule devise (validé à l'ajout).
        """
        total = Decimal("0.00")
        for item in cart.items.select_related("listing").all():
            total += item.listing.price * item.quantity
        return total

    # ---------------------------------------------------------
    # CART VALIDATION
    # ---------------------------------------------------------

    @staticmethod
    def validate_cart(*, cart):
        """
        Vérifie que le panier est achetable.
        - Panier actif
        - Non vide
        - Tous les listings sont PUBLISHED et stock suffisant
        - Une seule devise (implicite via add_item)
        """
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
        """
        Supprime les articles dont le listing n'est plus PUBLISHED ou en stock insuffisant.
        Retourne le cart nettoyé.
        """
        items = cart.items.select_related("listing").all()
        for item in items:
            listing = item.listing
            if listing.status != Listing.Status.PUBLISHED or listing.stock <= 0:
                item.delete()
            elif listing.stock < item.quantity:
                item.delete()
        return cart
