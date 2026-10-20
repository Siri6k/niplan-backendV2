# catalog/views/variant.py
from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from catalog.filters import VariantFilter
from catalog.models import (
    ProductMedia,
    ProductVariant,
    VariantAttributeValue,  # ✅ le bon modèle
)
from catalog.serializers import (
    ProductVariantSerializer,
    VariantDetailSerializer,
    VariantListSerializer,
    VariantBulkLookupSerializer,
)


# ---------- Helpers de prefetch ----------
def _variant_queryset(*, detail: bool = False):
    """
    Queryset ProductVariant avec prefetch adapté.
    ✅ On prefetch `variant_values` avec le bon modèle (VariantAttributeValue),
       pas ProductVariant (qui n'a ni `value` ni `variant`).
    """
    qs = (
        ProductVariant.objects.filter(is_active=True)
        .select_related("product")
        .prefetch_related(
            Prefetch(
                "variant_values",
                queryset=VariantAttributeValue.objects.select_related(
                    "value__attribute"
                ),
                to_attr="_prefetched_variant_values",
            ),
        )
    )
    if detail:
        qs = qs.prefetch_related(
            Prefetch("media", queryset=ProductMedia.objects.order_by("sort_order")),
        )
    else:
        qs = qs.prefetch_related(
            Prefetch(
                "media",
                queryset=ProductMedia.objects.order_by("-is_primary", "sort_order"),
            ),
        )
    return qs


# ---------- LISTE ----------
@extend_schema(
    tags=["Catalog"],
    summary="Liste paginée des variantes actives",
    description=(
        "Retourne les variantes actives avec attributs résumés et média principal. "
        "Filtrable, triable et recherchable."
    ),
    parameters=[
        OpenApiParameter(
            "attribute", str, description="Filtre attribut, ex: `Pointure:44`"
        ),
        OpenApiParameter("product", str, description="UUID du produit"),
        OpenApiParameter(
            "search", str, description="Recherche SKU / nom produit / valeur"
        ),
    ],
    responses={200: VariantListSerializer(many=True)},
)
class VariantListView(generics.ListAPIView):
    serializer_class = VariantListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = VariantFilter
    search_fields = ["sku", "product__name", "variant_values__value__value"]
    ordering_fields = ["created_at", "sku"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return _variant_queryset(detail=False).distinct()


# ---------- DÉTAIL par UUID ----------
@extend_schema(
    tags=["Catalog"],
    summary="Détail d'une variante par UUID",
    responses={200: VariantDetailSerializer},
)
class VariantDetailView(generics.RetrieveAPIView):
    serializer_class = VariantDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"  # ✅ UUID, pas SKU

    def get_queryset(self):
        return _variant_queryset(detail=True)


# ---------- DÉTAIL par SKU ----------
@extend_schema(
    tags=["Catalog"],
    summary="Récupérer une variante par SKU",
    responses={200: VariantDetailSerializer},
)
class VariantBySkuView(generics.RetrieveAPIView):
    serializer_class = VariantDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "sku"
    lookup_url_kwarg = "sku"

    def get_queryset(self):
        return _variant_queryset(detail=True)


# ---------- Variantes d'un produit ----------
@extend_schema(
    tags=["Catalog"],
    summary="Variantes d'un produit",
    responses={200: VariantListSerializer(many=True)},
)
class ProductVariantsView(generics.ListAPIView):
    serializer_class = VariantListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return _variant_queryset(detail=False).filter(
            product_id=self.kwargs["product_id"]
        )


# ---------- Facettes pour filtres UI ----------
@extend_schema(
    tags=["Catalog"],
    summary="Facettes d'attributs disponibles",
    description=(
        "Retourne les attributs (Pointure, Couleur, Taille…) et leurs valeurs "
        "possibles. Accepte `?product=<uuid>` pour restreindre à un produit."
    ),
    parameters=[OpenApiParameter("product", str)],
    responses={200: dict},
)
class VariantFacetsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # ✅ On part de VariantAttributeValue (qui a bien le FK `variant`)
        qs = VariantAttributeValue.objects.filter(variant__is_active=True)

        if product_id := request.query_params.get("product"):
            qs = qs.filter(variant__product_id=product_id)

        rows = (
            qs.select_related("value__attribute")
            .values_list("value__attribute__name", "value__value")
            .distinct()
            .order_by("value__attribute__name", "value__value")
        )

        facets: dict[str, list[str]] = {}
        for attr_name, value in rows:
            facets.setdefault(attr_name, []).append(value)
        return Response(facets)


# ---------- Autocomplete ----------
@extend_schema(
    tags=["Catalog"],
    summary="Autocomplete variantes",
    parameters=[OpenApiParameter("q", str, required=True)],
    responses={200: ProductVariantSerializer(many=True)},
)
class VariantAutocompleteView(generics.ListAPIView):
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        q = self.request.query_params.get("q", "").strip()
        if len(q) < 2:
            return ProductVariant.objects.none()

        # ✅ prefetch pour que `attribute_summary` (property) ne tire pas N+1
        return (
            ProductVariant.objects.filter(is_active=True, sku__icontains=q)
            .prefetch_related(
                Prefetch(
                    "variant_values",
                    queryset=VariantAttributeValue.objects.select_related(
                        "value__attribute"
                    ),
                    to_attr="_prefetched_variant_values",
                ),
            )
            .order_by("sku")[:20]
        )


# ---------- Bulk lookup ----------
@extend_schema(
    tags=["Catalog"],
    summary="Lookup bulk par SKUs",
    description="Récupère plusieurs variantes en une seule requête (panier, import).",
    request=VariantBulkLookupSerializer,
    responses={200: VariantDetailSerializer(many=True)},
)
class VariantBulkLookupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = VariantBulkLookupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        qs = _variant_queryset(detail=True).filter(sku__in=ser.validated_data["skus"])
        return Response(
            VariantDetailSerializer(qs, many=True).data,
            status=status.HTTP_200_OK,
        )
