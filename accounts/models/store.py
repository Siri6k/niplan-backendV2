# accounts/models/store.py

import uuid

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Store(models.Model):
    """
    Boutique appartenant à un vendeur.
    C'est l'entité commerciale visible publiquement sur la marketplace.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    seller = models.OneToOneField(
        "accounts.SellerProfile",
        on_delete=models.CASCADE,
        related_name="store",
        verbose_name=_("seller"),
    )

    # ─── Identité visuelle ───
    name = models.CharField(_("store name"), max_length=150, db_index=True)
    slug = models.SlugField(
        _("slug"),
        max_length=150,
        unique=True,
        db_index=True,
        help_text=_("Identifiant URL unique, généré automatiquement."),
    )
    description = models.TextField(_("description"), blank=True, max_length=2000)

    # ─── Média ───
    logo = models.ImageField(
        _("logo"),
        upload_to="stores/logos/%Y/%m/",
        blank=True,
        null=True,
    )
    banner = models.ImageField(
        _("banner"),
        upload_to="stores/banners/%Y/%m/",
        blank=True,
        null=True,
    )

    # ─── Contact & localisation ───
    phone = models.CharField(_("contact phone"), max_length=30, blank=True)
    city = models.CharField(_("city"), max_length=100, blank=True, db_index=True)
    address = models.TextField(_("address"), blank=True, max_length=500)

    # ─── Statut ───
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Désactive la boutique sans supprimer les données. "
            "Les listings deviennent invisibles."
        ),
    )

    # ─── Métadonnées ───
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "accounts_store"
        verbose_name = _("store")
        verbose_name_plural = _("stores")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug", "is_active"]),
            models.Index(fields=["city", "is_active"]),
            models.Index(fields=["name", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Store.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def owner_email(self) -> str:
        return self.seller.user.email

    @property
    def is_open(self) -> bool:
        """La boutique est ouverte si elle et son vendeur sont actifs."""
        return self.is_active and self.seller.user.is_active and self.seller.is_verified
