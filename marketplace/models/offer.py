import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Offer(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        COUNTERED = "COUNTERED", "Countered"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    listing = models.ForeignKey(
        "marketplace.Listing",
        on_delete=models.CASCADE,
        related_name="offers",
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="offers",
    )

    unit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01)
        ],
    )

    currency = models.CharField(
        max_length=3,
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    message = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    parent_offer = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="counter_offers",
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    responded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "marketplace_offers"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["listing", "status"]),
            models.Index(fields=["buyer", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.buyer} → "
            f"{self.listing} : "
            f"{self.unit_amount} {self.currency}"
        )

    @property
    def total_amount(self):
        return self.unit_amount * self.quantity