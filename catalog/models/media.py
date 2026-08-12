# catalog/models/media.py

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductMedia(models.Model):
    """
    Média attaché à un Product ou une ProductVariant.
    Stocke des URLs (Cloudinary) plutôt que des fichiers locaux.
    """

    class MediaType(models.TextChoices):
        IMAGE = "IMAGE", _("Image")
        VIDEO = "VIDEO", _("Vidéo")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="media",
        verbose_name=_("product"),
    )

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="media",
        null=True,
        blank=True,
        verbose_name=_("variant"),
        help_text=_("Laissez vide pour un média global au produit."),
    )

    media_type = models.CharField(
        _("media type"),
        max_length=10,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )

    url = models.URLField(
        _("URL"),
        max_length=1000,
    )

    thumbnail_url = models.URLField(
        _("thumbnail URL"),
        max_length=1000,
        blank=True,
    )

    alt_text = models.CharField(
        _("alt text"),
        max_length=255,
        blank=True,
        help_text=_("Description pour l'accessibilité et le SEO."),
    )

    is_primary = models.BooleanField(
        _("primary"),
        default=False,
        help_text=_("Image principale affichée en premier."),
    )

    sort_order = models.PositiveIntegerField(
        _("sort order"),
        default=0,
    )

    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )

    class Meta:
        db_table = "catalog_product_media"
        verbose_name = _("product media")
        verbose_name_plural = _("product media")
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["product", "sort_order"]),
            models.Index(fields=["variant", "sort_order"]),
            models.Index(fields=["media_type", "is_primary"]),
        ]

    def __str__(self) -> str:
        prefix = f"{self.product.name}"
        if self.variant:
            prefix = f"{self.variant.sku}"
        return f"{prefix} — {self.get_media_type_display()}"
