# catalog/views/category.py

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from catalog.models import Category
from catalog.serializers import CategorySerializer, CategoryTreeSerializer


@extend_schema(
    tags=["Catalog"],
    summary="Liste des catégories",
    description="Retourne l'arborescence des catégories actives (racines + enfants).",
    responses={200: CategorySerializer(many=True)},
)
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True, parent=None).prefetch_related(
        "children"
    )
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


@extend_schema(
    tags=["Catalog"],
    summary="Détail d'une catégorie",
    description="Retourne une catégorie et ses produits associés.",
    responses={200: CategorySerializer},
)
class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
