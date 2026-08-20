# cart/models/cart_item.py
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class CartItem(models.Model):
    """
    Ligne d'un panier, liée à une annonce (Listing) précise.
    Le prix et le vendeur sont hérités du Listing au moment du checkout.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    cart = models.ForeignKey(
        "cart.Cart",
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("panier"),
    )

    listing = models.ForeignKey(
        "marketplace.Listing",
        on_delete=models.PROTECT,
        related_name="cart_items",
        verbose_name=_("annonce"),
    )

    quantity = models.PositiveIntegerField(
        _("quantité"),
        default=1,
    )

    created_at = models.DateTimeField(
        _("créé le"),
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        _("mis à jour le"),
        auto_now=True,
    )

    class Meta:
        db_table = "cart_items"
        verbose_name = _("ligne de panier")
        verbose_name_plural = _("lignes de panier")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "listing"],
                name="unique_listing_per_cart",
            )
        ]

    def __str__(self) -> str:
        return f"{self.listing.title} × {self.quantity}"

    @property
    def subtotal(self):
        """
        Sous-total courant de la ligne.

        Le panier utilise toujours le prix actuel du Listing.
        Le prix définitif sera figé dans OrderItem lors du checkout.
        """
        return self.listing.price * self.quantity
