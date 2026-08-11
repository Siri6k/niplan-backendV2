# accounts/models/user.py

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model centralisant l'identité Niplan.
    Supporte email, téléphone et OAuth (Google) via un système d'identité unifié.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    # ─── Identité ───
    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
        error_messages={
            "unique": _("Un utilisateur avec cet email existe déjà."),
        },
    )
    phone_number = models.CharField(
        _("phone number"),
        max_length=30,
        blank=True,
        db_index=True,
        help_text=_("Format international, ex: +243..."),
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    # ─── Statut ───
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Désactive l'utilisateur au lieu de le supprimer. "
            "Les objets liés restent intacts."
        ),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Accès à l'admin Django."),
    )

    # ─── Métadonnées ───
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)

    # ─── Configuration auth ───
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        db_table = "accounts_user"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email", "is_active"]),
            models.Index(fields=["phone_number", "is_active"]),
            models.Index(fields=["date_joined"]),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_seller(self) -> bool:
        """Vérifie si l'utilisateur possède un profil vendeur actif."""
        return hasattr(self, "seller_profile") and self.seller_profile is not None
