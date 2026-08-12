# catalog/views/product.py

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, permissions

from catalog.models import Product
from catalog.serializers import ProductDetailSerializer, ProductListSerializer


@extend_schema(
    tags=["Catalog"],
    summary="Liste des produits",
    description="Retourne les produits actifs. Filtres: category, brand, status, search.",
    responses={200: ProductListSerializer(many=True)},
)
class ProductListView(generics.ListAPIView):
    queryset = (
        Product.objects.filter(is_active=True, status="ACTIVE")
        .select_related("category")
        .prefetch_related("media", "variants")
    )
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category__slug", "brand", "status"]
    search_fields = ["name", "brand", "model", "description"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]


@extend_schema(
    tags=["Catalog"],
    summary="Détail d'un produit",
    description="Retourne le produit avec ses variants, médias et spécifications.",
    responses={200: ProductDetailSerializer},
)
class ProductDetailView(generics.RetrieveAPIView):
    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("variants__variant_values__value__attribute", "media")
    )
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
