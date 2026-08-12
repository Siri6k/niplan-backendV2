# marketplace/models/listing.py

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Listing(models.Model):
    """
    Offre commerciale d'un vendeur sur la marketplace.
    Un Listing = un Variant du catalogue + un prix + un stock + un vendeur.
    """

    class Condition(models.TextChoices):
        NEW = "NEW", _("Neuf")
        USED = "USED", _("Occasion")
        REFURBISHED = "REFURBISHED", _("Reconditionné")

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Brouillon")
        PENDING = "PENDING", _("En attente de validation")
        PUBLISHED = "PUBLISHED", _("Publié")
        PAUSED = "PAUSED", _("En pause")
        SOLD_OUT = "SOLD_OUT", _("Épuisé")
        ARCHIVED = "ARCHIVED", _("Archivé")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    seller = models.ForeignKey(
        "accounts.SellerProfile",
        on_delete=models.PROTECT,
        related_name="listings",
        verbose_name=_("seller"),
    )

    store = models.ForeignKey(
        "accounts.Store",
        on_delete=models.PROTECT,
        related_name="listings",
        verbose_name=_("store"),
    )

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="listings",
        verbose_name=_("product variant"),
    )

    title = models.CharField(
        _("title"),
        max_length=255,
    )

    description = models.TextField(
        _("description"),
        blank=True,
    )

    price = models.DecimalField(
        _("price"),
        max_digits=12,
        decimal_places=2,
    )

    currency = models.CharField(
        _("currency"),
        max_length=3,
        default="USD",
    )

    condition = models.CharField(
        _("condition"),
        max_length=20,
        choices=Condition.choices,
        default=Condition.NEW,
    )

    stock = models.PositiveIntegerField(
        _("stock"),
        default=0,
    )

    location = models.CharField(
        _("location"),
        max_length=150,
        blank=True,
    )

    is_negotiable = models.BooleanField(
        _("negotiable"),
        default=False,
    )

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    published_at = models.DateTimeField(
        _("published at"),
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        _("updated at"),
        auto_now=True,
    )

    class Meta:
        db_table = "marketplace_listings"
        verbose_name = _("listing")
        verbose_name_plural = _("listings")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["seller", "status"]),
            models.Index(fields=["store", "status"]),
            models.Index(fields=["variant", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["price", "status"]),
            models.Index(fields=["condition", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.store.name})"

    @property
    def is_available(self) -> bool:
        return self.status == self.Status.PUBLISHED and self.stock > 0
