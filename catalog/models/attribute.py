# catalog/models/attribute.py

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductAttribute(models.Model):
    """
    Type d'attribut défini pour un produit.
    Ex: Color, Storage, Size, RAM, Processor...
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name=_("product"),
    )

    name = models.CharField(
        _("name"),
        max_length=50,
        help_text=_("Ex: Color, Storage, Size, RAM..."),
    )

    sort_order = models.PositiveIntegerField(
        _("sort order"),
        default=0,
    )

    class Meta:
        db_table = "catalog_product_attributes"
        verbose_name = _("product attribute")
        verbose_name_plural = _("product attributes")
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "name"],
                name="unique_attribute_per_product",
                violation_error_message=_(
                    "Ce produit possède déjà un attribut avec ce nom."
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.name}"


class AttributeValue(models.Model):
    """
    Valeur possible pour un attribut.
    Ex: Black, 256GB, 42, Core i7...
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name=_("attribute"),
    )

    value = models.CharField(
        _("value"),
        max_length=100,
    )

    sort_order = models.PositiveIntegerField(
        _("sort order"),
        default=0,
    )

    class Meta:
        db_table = "catalog_attribute_values"
        verbose_name = _("attribute value")
        verbose_name_plural = _("attribute values")
        ordering = ["sort_order", "value"]
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "value"],
                name="unique_value_per_attribute",
                violation_error_message=_(
                    "Cette valeur existe déjà pour cet attribut."
                ),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.attribute.name}: {self.value}"
