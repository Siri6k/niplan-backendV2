from rest_framework import serializers

from catalog.models import ProductVariant
from catalog.serializers.media import ProductMediaSerializer


# ---------- LISTE (léger) ----------
class ProductVariantSerializer(serializers.ModelSerializer):
    """Version minimale : utilisée pour les listes légères (autocomplete, sélecteurs)."""

    attribute_summary = serializers.CharField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ("id", "sku", "is_active", "attribute_summary", "created_at")


class VariantListSerializer(serializers.ModelSerializer):
    """Version optimisée pour la liste paginée : 1 seul média (le principal)."""

    attribute_summary = serializers.CharField(read_only=True)
    display_title = serializers.CharField(read_only=True)
    primary_media = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "is_active",
            "attribute_summary",
            "display_title",
            "primary_media",
            "created_at",
        )

    def get_primary_media(self, obj: ProductVariant):
        # `obj.media.all()` est pré-chargé via Prefetch → 0 requête supplémentaire
        medias = list(obj.media.all())
        if not medias:
            return None
        primary = next((m for m in medias if m.is_primary), medias[0])
        return ProductMediaSerializer(primary).data


# ---------- DÉTAIL (complet) — ta version, légèrement optimisée ----------
class VariantDetailSerializer(serializers.ModelSerializer):
    attribute_summary = serializers.CharField(read_only=True)
    display_title = serializers.CharField(read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)
    values = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "is_active",
            "attribute_summary",
            "display_title",
            "media",
            "values",
            "created_at",
        )

    def get_values(self, obj: ProductVariant):
        # On préfère itérer sur `obj.variant_values.all()` si le prefetch a été fait,
        # sinon fallback sur le related manager (garde ta logique fonctionnelle).
        variant_values = getattr(obj, "_prefetched_variant_values", None)
        if variant_values is None:
            variant_values = obj.variant_values.select_related("value__attribute").all()

        return [
            {
                "attribute": v.value.attribute.name,
                "value": v.value.value,
            }
            for v in variant_values
        ]


# ---------- Bulk lookup par SKUs ----------
class VariantBulkLookupSerializer(serializers.Serializer):
    skus = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        max_length=100,
    )
