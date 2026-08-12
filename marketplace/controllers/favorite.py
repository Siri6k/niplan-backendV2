from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from marketplace.models import Listing
from marketplace.serializers import FavoriteSerializer
from marketplace.services.favorite_service import (
    FavoriteService,
)


@extend_schema(
    tags=["Marketplace"],
    summary="Ajout et suppression d'une annonce aux favoris",
    description="POST : ajouter une annonce aux favoris (utilisateur authentifié). DELETE : supprimer une annonce des favoris (utilisateur authentifié).",
    responses={
        201: FavoriteSerializer,
        204: None,
        400: "Bad Request",
    },
)
class ListingFavoriteView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        listing = get_object_or_404(
            Listing,
            pk=pk,
        )

        favorite = FavoriteService.add_favorite(
            user=request.user,
            listing=listing,
        )

        return Response(
            FavoriteSerializer(favorite).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, pk):

        listing = get_object_or_404(
            Listing,
            pk=pk,
        )

        FavoriteService.remove_favorite(
            user=request.user,
            listing=listing,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Marketplace"],
    summary="Liste des annonces favorites de l'utilisateur",
    description="GET : liste des annonces favorites de l'utilisateur authentifié.",
    responses={200: FavoriteSerializer(many=True)},
)
class FavoriteListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        favorites = request.user.favorites.select_related(
            "listing",
            "listing__store",
            "listing__variant",
            "listing__variant__product",
        )

        serializer = FavoriteSerializer(
            favorites,
            many=True,
        )

        return Response(serializer.data)
