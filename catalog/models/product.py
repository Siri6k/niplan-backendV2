# catalog/models/product.py

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    """
    Identité générique d'un produit dans le catalogue.
    Ne contient PAS de prix, stock, vendeur ou localisation.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Brouillon")
        ACTIVE = "ACTIVE", _("Actif")
        ARCHIVED = "ARCHIVED", _("Archivé")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("category"),
    )

    name = models.CharField(
        _("name"),
        max_length=200,
        db_index=True,
    )

    brand = models.CharField(
        _("brand"),
        max_length=100,
        blank=True,
        db_index=True,
    )

    model = models.CharField(
        _("model"),
        max_length=100,
        blank=True,
        db_index=True,
    )

    description = models.TextField(
        _("description"),
        blank=True,
    )

    slug = models.SlugField(
        _("slug"),
        max_length=250,
        unique=True,
        db_index=True,
    )

    specifications = models.JSONField(
        _("specifications"),
        default=dict,
        blank=True,
        help_text=_("Caractéristiques génériques : écran, RAM, moteur, etc."),
    )

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    is_active = models.BooleanField(
        _("active"),
        default=True,
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
        db_table = "catalog_products"
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["brand", "is_active"]),
            models.Index(fields=["status", "is_active"]),
            models.Index(fields=["slug", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        """Samsung Galaxy S24 ou juste le nom si brand vide."""
        if self.brand:
            return f"{self.brand} {self.name}"
        return self.name
