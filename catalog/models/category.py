# catalog/models/category.py

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Catégorie hiérarchique du catalogue Niplan.
    Supporte les niveaux de profondeur illimités (parent → children).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    name = models.CharField(
        _("name"),
        max_length=100,
        db_index=True,
    )

    slug = models.SlugField(
        _("slug"),
        max_length=120,
        unique=True,
        db_index=True,
        help_text=_("Identifiant URL unique."),
    )

    description = models.TextField(
        _("description"),
        blank=True,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("parent category"),
        help_text=_("Laisser vide pour une catégorie racine."),
    )

    image = models.ImageField(
        _("image"),
        upload_to="categories/%Y/%m/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Inactive les sous-catégories aussi visuellement."),
    )

    sort_order = models.PositiveIntegerField(
        _("sort order"),
        default=0,
        help_text=_("Ordre d'affichage, du plus petit au plus grand."),
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
        db_table = "catalog_categories"
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["parent", "is_active"]),
            models.Index(fields=["is_active", "sort_order"]),
            models.Index(fields=["slug", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def full_path(self) -> str:
        """Retourne le chemin hiérarchique : Électronique > Téléphones > Smartphones"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def depth(self) -> int:
        """Profondeur dans l'arbre (0 = racine)."""
        if self.parent is None:
            return 0
        return self.parent.depth + 1
