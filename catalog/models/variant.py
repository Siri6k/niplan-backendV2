# catalog/models/variant.py

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .attribute import AttributeValue


class ProductVariant(models.Model):
    """
    Variante concrète d'un produit.
    Ex: Samsung S24 — Black — 256GB.
    Le prix et le vendeur ne sont PAS ici (ce sera dans Listing).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="variants",
        verbose_name=_("product"),
    )

    sku = models.CharField(
        _("SKU"),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Référence unique de la variante."),
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
        db_table = "catalog_product_variants"
        verbose_name = _("product variant")
        verbose_name_plural = _("product variants")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.product.name} ({self.sku})"

    @property
    def attribute_summary(self) -> str:
        """Black / 256GB / 8GB"""
        values = self.attribute_values.select_related("attribute").all()
        return " / ".join([str(v) for v in values])

    @property
    def display_title(self) -> str:
        """Samsung Galaxy S24 — Black / 256GB"""
        base = self.product.display_name
        summary = self.attribute_summary
        return f"{base} — {summary}" if summary else base


class VariantAttributeValue(models.Model):
    """
    Lie une variante à ses valeurs d'attributs.
    Ex: Variant 'S24-256-BLK' → Color=Black, Storage=256GB.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="variant_values",
        verbose_name=_("variant"),
    )

    value = models.ForeignKey(
        AttributeValue,
        on_delete=models.CASCADE,
        related_name="variant_assignments",
        verbose_name=_("attribute value"),
    )

    class Meta:
        db_table = "catalog_variant_attribute_values"
        verbose_name = _("variant attribute value")
        verbose_name_plural = _("variant attribute values")
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "value"],
                name="unique_value_per_variant",
                violation_error_message=_(
                    "Cette valeur est déjà assignée à cette variante."
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku} → {self.value}"
