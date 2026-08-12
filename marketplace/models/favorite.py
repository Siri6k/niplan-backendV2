import uuid

from django.conf import settings
from django.db import models


class Favorite(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    listing = models.ForeignKey(
        "marketplace.Listing",
        on_delete=models.CASCADE,
        related_name="favorites",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "marketplace_favorites"

        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "listing",
                ],
                name="unique_user_listing_favorite",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "created_at",
                ]
            ),
            models.Index(
                fields=[
                    "listing",
                    "created_at",
                ]
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.listing}"
