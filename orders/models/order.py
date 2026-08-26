import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    """
    Commande créée à partir d'un panier.

    Une commande appartient à un seul vendeur.
    Un panier multi-vendeurs peut donc générer plusieurs commandes.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", _("En attente")
        CONFIRMED = "CONFIRMED", _("Confirmée")
        PROCESSING = "PROCESSING", _("En préparation")
        SHIPPED = "SHIPPED", _("Expédiée")
        DELIVERED = "DELIVERED", _("Livrée")
        CANCELLED = "CANCELLED", _("Annulée")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("acheteur"),
    )

    seller = models.ForeignKey(
        "accounts.SellerProfile",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("vendeur"),
    )

    status = models.CharField(
        _("statut"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    currency = models.CharField(
        _("devise"),
        max_length=3,
    )

    subtotal = models.DecimalField(
        _("sous-total"),
        max_digits=12,
        decimal_places=2,
    )

    shipping_cost = models.DecimalField(
        _("frais de livraison"),
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total = models.DecimalField(
        _("total"),
        max_digits=12,
        decimal_places=2,
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
        db_table = "orders"
        verbose_name = _("commande")
        verbose_name_plural = _("commandes")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["buyer", "status"],
                name="order_buyer_status_idx",
            ),
            models.Index(
                fields=["seller", "status"],
                name="order_seller_status_idx",
            ),
            models.Index(
                fields=["created_at"],
                name="order_created_at_idx",
            ),
        ]

    def __str__(self):
        return f"Commande {self.id}"
