# accounts/models/profile.py

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    """
    Profil public de l'utilisateur (acheteur).
    Aucune donnée commerciale ici — uniquement l'identité sociale.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("user"),
    )

    # ─── Média ───
    avatar = models.ImageField(
        _("avatar"),
        upload_to="accounts/avatars/%Y/%m/",
        blank=True,
        null=True,
    )

    # ─── Bio ───
    bio = models.TextField(_("bio"), blank=True, max_length=500)

    # ─── Localisation ───
    city = models.CharField(_("city"), max_length=100, blank=True)
    country = models.CharField(
        _("country"),
        max_length=2,
        blank=True,
        help_text=_("Code ISO 3166-1 alpha-2, ex: CD, FR, US"),
    )

    # ─── Préférences ───
    preferred_currency = models.CharField(
        _("preferred currency"),
        max_length=3,
        default="USD",
        help_text=_("Code ISO 4217, ex: USD, CDF, EUR"),
    )
    language = models.CharField(
        _("language"),
        max_length=10,
        default="fr",
        help_text=_("Code IETF BCP 47, ex: fr, en, sw"),
    )

    # ─── Métadonnées ───
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "accounts_profile"
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")
        indexes = [
            models.Index(fields=["country", "city"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self) -> str:
        return f"Profile of {self.user.email}"