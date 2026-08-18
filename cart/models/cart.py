# cart/models/cart.py
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Cart(models.Model):
    """
    Panier d'un acheteur.
    Un acheteur peut avoir plusieurs paniers dans le temps,
    mais un seul panier ACTIVE à la fois.
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Actif")
        CHECKED_OUT = "CHECKED_OUT", _("Converti en commande")
        ABANDONED = "ABANDONED", _("Abandonné")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="carts",
        verbose_name=_("acheteur"),
    )

    status = models.CharField(
        _("statut"),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
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
    last_accessed_at = models.DateTimeField(
        _("dernier accès"),
        default=timezone.now,
        help_text=_("Date de dernière activité sur le panier"),
    )

    class Meta:
        db_table = "cart_carts"
        verbose_name = _("panier")
        verbose_name_plural = _("paniers")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["buyer"],
                condition=models.Q(status="ACTIVE"),
                name="unique_active_cart_per_buyer",
            )
        ]

    def __str__(self) -> str:
        return f"Panier {self.id} — {self.buyer.email}"
