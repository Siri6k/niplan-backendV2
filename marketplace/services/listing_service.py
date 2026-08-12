# marketplace/services/listing_service.py

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import SellerProfile, Store
from catalog.models import Product, ProductVariant

from marketplace.models import Listing


class ListingService:
    """
    Service métier pour la gestion des annonces (Listing).
    Centralise les règles de sécurité, de validation et de workflow.
    """

    @staticmethod
    def get_seller(user) -> SellerProfile:
        """Retourne le SellerProfile associé à l'utilisateur."""
        try:
            return user.seller_profile
        except SellerProfile.DoesNotExist:
            raise ValidationError("Cet utilisateur ne possède pas de profil vendeur.")

    @staticmethod
    def validate_store_ownership(store: Store, seller: SellerProfile) -> None:
        """Vérifie que la boutique appartient bien au vendeur."""
        if store.seller_id != seller.id:
            raise ValidationError("Cette boutique n'appartient pas à ce vendeur.")

    @staticmethod
    def validate_variant(variant: ProductVariant) -> None:
        """Vérifie que la variante et son produit peuvent être listés."""
        if not variant.is_active:
            raise ValidationError("Cette variante n'est pas active.")

        if variant.product.status != Product.Status.ACTIVE:
            raise ValidationError("Le produit associé n'est pas actif.")

        if not variant.product.is_active:
            raise ValidationError("Le produit associé est désactivé.")

    @staticmethod
    @transaction.atomic
    def create_listing(
        *,
        user,
        store: Store,
        variant: ProductVariant,
        title: str,
        price: Decimal,
        currency: str = "USD",
        condition: str = Listing.Condition.NEW,
        stock: int = 0,
        location: str = "",
        description: str = "",
        is_negotiable: bool = False,
    ) -> Listing:
        """Crée une annonce en vérifiant toutes les règles métier."""

        seller = ListingService.get_seller(user)
        ListingService.validate_store_ownership(store, seller)
        ListingService.validate_variant(variant)

        if price <= 0:
            raise ValidationError("Le prix doit être supérieur à zéro.")

        if stock < 0:
            raise ValidationError("Le stock ne peut pas être négatif.")

        listing = Listing.objects.create(
            seller=seller,
            store=store,
            variant=variant,
            title=title,
            description=description,
            price=price,
            currency=currency,
            condition=condition,
            stock=stock,
            location=location,
            is_negotiable=is_negotiable,
            status=Listing.Status.DRAFT,
        )

        return listing

    @staticmethod
    @transaction.atomic
    def update_listing(*, listing: Listing, user, **validated_data) -> Listing:
        seller = ListingService.get_seller(user)

        if listing.seller_id != seller.id:
            raise ValidationError("Vous ne pouvez pas modifier cette annonce.")

        if listing.status == Listing.Status.ARCHIVED:
            raise ValidationError("Une annonce archivée ne peut pas être modifiée.")

        allowed_fields = [
            "title",
            "description",
            "price",
            "currency",
            "condition",
            "stock",
            "location",
            "is_negotiable",
        ]
        for field, value in validated_data.items():
            if field in allowed_fields:
                setattr(listing, field, value)

        listing.save()
        return listing

    @staticmethod
    @transaction.atomic
    def publish_listing(*, listing: Listing, user) -> Listing:
        """Publie une annonce (DRAFT → PUBLISHED)."""

        seller = ListingService.get_seller(user)

        if listing.seller_id != seller.id:
            raise ValidationError("Vous ne pouvez pas publier cette annonce.")

        if listing.status not in [
            Listing.Status.DRAFT,
            Listing.Status.PENDING,
            Listing.Status.PAUSED,
        ]:
            raise ValidationError(
                "Cette annonce ne peut pas être publiée depuis son état actuel."
            )

        if listing.stock <= 0:
            raise ValidationError("Impossible de publier une annonce sans stock.")

        listing.status = Listing.Status.PUBLISHED
        listing.published_at = timezone.now()
        listing.save(update_fields=["status", "published_at", "updated_at"])

        return listing

    @staticmethod
    @transaction.atomic
    def pause_listing(*, listing: Listing, user) -> Listing:
        """Met en pause une annonce publiée."""

        seller = ListingService.get_seller(user)

        if listing.seller_id != seller.id:
            raise ValidationError("Vous ne pouvez pas modifier cette annonce.")

        if listing.status != Listing.Status.PUBLISHED:
            raise ValidationError("Seule une annonce publiée peut être mise en pause.")

        listing.status = Listing.Status.PAUSED
        listing.save(update_fields=["status", "updated_at"])

        return listing

    @staticmethod
    @transaction.atomic
    def archive_listing(*, listing: Listing, user) -> Listing:
        """Archive une annonce."""

        seller = ListingService.get_seller(user)

        if listing.seller_id != seller.id:
            raise ValidationError("Vous ne pouvez pas archiver cette annonce.")

        if listing.status == Listing.Status.ARCHIVED:
            raise ValidationError("Cette annonce est déjà archivée.")

        listing.status = Listing.Status.ARCHIVED
        listing.save(update_fields=["status", "updated_at"])

        return listing
