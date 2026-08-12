from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from marketplace.models import Favorite, Listing


class FavoriteService:

    @staticmethod
    @transaction.atomic
    def add_favorite(*, user, listing):

        if not user.is_authenticated:
            raise ValidationError("Authentification requise.")

        if listing.status != Listing.Status.PUBLISHED:
            raise ValidationError(
                "Seule une annonce publiée peut être ajoutée aux favoris."
            )

        try:
            favorite = Favorite.objects.create(
                user=user,
                listing=listing,
            )

        except IntegrityError:
            raise ValidationError("Cette annonce est déjà dans vos favoris.")

        return favorite

    @staticmethod
    def remove_favorite(*, user, listing):

        deleted, _ = Favorite.objects.filter(
            user=user,
            listing=listing,
        ).delete()

        if deleted == 0:
            raise ValidationError("Cette annonce ne figure pas dans vos favoris.")

    @staticmethod
    def is_favorite(*, user, listing):

        if not user.is_authenticated:
            return False

        return Favorite.objects.filter(
            user=user,
            listing=listing,
        ).exists()
