# catalog/views/variant.py

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from catalog.models import ProductVariant
from catalog.serializers import VariantDetailSerializer


@extend_schema(
    tags=["Catalog"],
    summary="Détail d'une variante",
    description="Retourne une variante avec ses attributs, médias et titre complet.",
    responses={200: VariantDetailSerializer},
)
class VariantDetailView(generics.RetrieveAPIView):
    queryset = (
        ProductVariant.objects.filter(is_active=True)
        .select_related("product")
        .prefetch_related("variant_values__value__attribute", "media")
    )
    serializer_class = VariantDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "sku"
