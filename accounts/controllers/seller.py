from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from accounts.models import SellerProfile, Store
from accounts.permissions import IsSeller
from accounts.serializers import (
    BecomeSellerSerializer,
    SellerProfileSerializer,
    StoreCreateUpdateSerializer,
    StoreSerializer,
)


@extend_schema(
    tags=["Sellers"],
    summary="Devenir vendeur",
    description="Transforme un compte acheteur en vendeur. Crée un SellerProfile avec statut PENDING.",
    request=BecomeSellerSerializer,
    responses={
        201: OpenApiResponse(description="Profil vendeur créé"),
        400: OpenApiResponse(description="Déjà vendeur ou données invalides"),
    },
)
class BecomeSellerView(generics.CreateAPIView):
    serializer_class = BecomeSellerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        seller = serializer.save()
        return Response(
            SellerProfileSerializer(seller).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Sellers"],
    summary="Mon profil vendeur",
    description="Retourne les infos vendeur (type, vérification, note, ventes).",
    responses={200: SellerProfileSerializer},
)
class SellerMeView(generics.RetrieveAPIView):
    serializer_class = SellerProfileSerializer
    permission_classes = [IsSeller]

    def get_object(self):
        return self.request.user.seller_profile


# ─── StoreViewSet : décorer chaque action manuellement ───
@extend_schema_view(
    retrieve=extend_schema(
        tags=["Sellers"],
        summary="Ma boutique",
        description="Retourne la boutique du vendeur connecté.",
        responses={
            200: StoreSerializer,
            404: OpenApiResponse(description="Aucune boutique"),
        },
    ),
    create=extend_schema(
        tags=["Sellers"],
        summary="Créer ma boutique",
        description="Crée une boutique liée au SellerProfile. Un vendeur = une seule boutique.",
        request=StoreCreateUpdateSerializer,
        responses={
            201: StoreSerializer,
            400: OpenApiResponse(description="Boutique déjà existante"),
        },
    ),
    partial_update=extend_schema(
        tags=["Sellers"],
        summary="Modifier ma boutique",
        description="Met à jour les infos de la boutique (nom, description, ville, etc.).",
        request=StoreCreateUpdateSerializer,
        responses={
            200: StoreSerializer,
            404: OpenApiResponse(description="Boutique introuvable"),
        },
    ),
)
class StoreViewSet(ModelViewSet):
    """
    GET    /seller/store/  → voir ma boutique
    POST   /seller/store/  → créer ma boutique
    PATCH  /seller/store/  → modifier ma boutique
    """

    permission_classes = [IsSeller]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return StoreCreateUpdateSerializer
        return StoreSerializer

    def get_object(self):
        """Un vendeur n'a qu'une seule boutique."""
        try:
            store = self.request.user.seller_profile.store
            return store
        except Store.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        """GET /seller/store/"""
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Vous n'avez pas encore de boutique."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """POST /seller/store/"""
        if hasattr(request.user.seller_profile, "store"):
            return Response(
                {"detail": "Vous avez déjà une boutique."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(seller=request.user.seller_profile)
        return Response(
            StoreSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        """PATCH /seller/store/"""
        instance = self.get_object()
        if instance is None:
            return Response(
                {"detail": "Boutique introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StoreSerializer(instance).data)
