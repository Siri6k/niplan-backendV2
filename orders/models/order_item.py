import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class OrderItem(models.Model):
    """
    Article d'une commande.

    Les informations importantes du listing sont copiées au moment
    de la commande afin de conserver un historique fiable.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", _("En attente")
        PROCESSING = "PROCESSING", _("En préparation")
        SHIPPED = "SHIPPED", _("Expédié")
        DELIVERED = "DELIVERED", _("Livré")
        CANCELLED = "CANCELLED", _("Annulé")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("commande"),
    )

    listing = models.ForeignKey(
        "marketplace.Listing",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name=_("annonce"),
    )

    seller = models.ForeignKey(
        "accounts.SellerProfile",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name=_("vendeur"),
    )

    product_name = models.CharField(
        _("nom du produit"),
        max_length=255,
    )

    variant_name = models.CharField(
        _("nom de la variante"),
        max_length=255,
        blank=True,
    )

    sku = models.CharField(
        _("SKU"),
        max_length=100,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        _("quantité"),
    )

    unit_price = models.DecimalField(
        _("prix unitaire"),
        max_digits=12,
        decimal_places=2,
    )

    subtotal = models.DecimalField(
        _("sous-total"),
        max_digits=12,
        decimal_places=2,
    )
    # ✅ NOUVEAU CHAMP
    status = models.CharField(
        _("statut"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
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
        db_table = "order_items"
        verbose_name = _("article de commande")
        verbose_name_plural = _("articles de commande")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"
