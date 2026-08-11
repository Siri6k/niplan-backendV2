# accounts/models/seller.py

import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class SellerType(models.TextChoices):
    INDIVIDUAL = "INDIVIDUAL", _("Particulier")
    BUSINESS = "BUSINESS", _("Entreprise")
    PROFESSIONAL = "PROFESSIONAL", _("Professionnel")


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", _("En attente")
    IN_REVIEW = "IN_REVIEW", _("En cours de vérification")
    VERIFIED = "VERIFIED", _("Vérifié")
    REJECTED = "REJECTED", _("Rejeté")
    SUSPENDED = "SUSPENDED", _("Suspendu")


class SellerProfile(models.Model):
    """
    Profil vendeur lié à un utilisateur existant.
    Un même compte peut être à la fois acheteur et vendeur.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_profile",
        verbose_name=_("user"),
    )

    # ─── Type & statut ───
    seller_type = models.CharField(
        _("seller type"),
        max_length=20,
        choices=SellerType.choices,
        default=SellerType.INDIVIDUAL,
        db_index=True,
    )
    verification_status = models.CharField(
        _("verification status"),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )

    # ─── Données dérivées (maintenues par un service) ───
    # Ces champs ne doivent JAMAIS être modifiés directement par les vues.
    # Ils sont mis à jour via des signaux ou des tâches async (Celery).
    rating = models.DecimalField(
        _("rating"),
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)],
        help_text=_("Note moyenne calculée à partir des avis clients."),
    )
    total_sales = models.PositiveIntegerField(
        _("total sales"),
        default=0,
        help_text=_("Nombre total de commandes finalisées."),
    )

    # ─── Métadonnées ───
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "accounts_seller_profile"
        verbose_name = _("seller profile")
        verbose_name_plural = _("seller profiles")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["seller_type", "verification_status"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["total_sales"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=0.00, rating__lte=5.00),
                name="seller_rating_range",
                violation_error_message=_("La note doit être entre 0.00 et 5.00."),
            ),
        ]

    def __str__(self) -> str:
        return f"Seller: {self.user.full_name} ({self.seller_type})"

    @property
    def is_verified(self) -> bool:
        return self.verification_status == VerificationStatus.VERIFIED

    @property
    def can_sell(self) -> bool:
        """Un vendeur peut vendre s'il est vérifié et actif."""
        return self.is_verified and self.user.is_active
