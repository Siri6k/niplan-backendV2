from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from marketplace.models import Listing, Offer


class OfferService:

    @staticmethod
    @transaction.atomic
    def create_offer(
        *,
        buyer,
        listing,
        unit_amount,
        quantity=1,
        message="",
    ):
        if not buyer.is_authenticated:
            raise ValidationError("Authentification requise.")

        if listing.status != Listing.Status.PUBLISHED:
            raise ValidationError("Cette annonce n'accepte pas les offres.")

        if listing.seller.user_id == buyer.id:
            raise ValidationError(
                "Vous ne pouvez pas faire une offre sur votre propre annonce."
            )

        if quantity < 1:
            raise ValidationError("La quantité doit être supérieure à zéro.")

        if quantity > listing.stock:
            raise ValidationError("La quantité demandée dépasse le stock disponible.")

        if unit_amount <= 0:
            raise ValidationError("Le montant unitaire doit être supérieur à zéro.")

        offer = Offer.objects.create(
            listing=listing,
            buyer=buyer,
            unit_amount=unit_amount,
            currency=listing.currency,
            quantity=quantity,
            message=message,
            status=Offer.Status.PENDING,
        )

        return offer

    @staticmethod
    @transaction.atomic
    def accept_offer(*, offer, user):
        if offer.listing.seller.user_id != user.id:
            raise ValidationError("Seul le vendeur peut accepter cette offre.")

        if offer.status != Offer.Status.PENDING:
            raise ValidationError("Cette offre n'est plus en attente.")

        offer.status = Offer.Status.ACCEPTED
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at", "updated_at"])

        return offer

    @staticmethod
    @transaction.atomic
    def reject_offer(*, offer, user):
        if offer.listing.seller.user_id != user.id:
            raise ValidationError("Seul le vendeur peut refuser cette offre.")

        if offer.status != Offer.Status.PENDING:
            raise ValidationError("Cette offre n'est plus en attente.")

        offer.status = Offer.Status.REJECTED
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at", "updated_at"])

        return offer

    @staticmethod
    @transaction.atomic
    def cancel_offer(*, offer, user):
        if offer.buyer_id != user.id:
            raise ValidationError("Seul l'acheteur peut annuler cette offre.")

        if offer.status != Offer.Status.PENDING:
            raise ValidationError("Cette offre ne peut plus être annulée.")

        offer.status = Offer.Status.CANCELLED
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at", "updated_at"])

        return offer

    @staticmethod
    @transaction.atomic
    def counter_offer(*, offer, user, unit_amount, message=""):
        if offer.status != Offer.Status.PENDING:
            raise ValidationError("Cette offre n'est plus active.")

        listing = offer.listing

        is_seller = listing.seller.user_id == user.id
        is_buyer = offer.buyer_id == user.id

        if not is_seller and not is_buyer:
            raise ValidationError("Vous ne participez pas à cette négociation.")

        counter = Offer.objects.create(
            listing=listing,
            buyer=offer.buyer,
            unit_amount=unit_amount,
            currency=listing.currency,
            quantity=offer.quantity,
            message=message,
            status=Offer.Status.PENDING,
            parent_offer=offer,
        )

        offer.status = Offer.Status.COUNTERED
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at", "updated_at"])

        return counter
