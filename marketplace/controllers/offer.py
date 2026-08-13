from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from marketplace.serializers.listing import ListingReadSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from marketplace.models import Listing, Offer
from marketplace.serializers.offer import (
    OfferActionSerializer,
    OfferCreateSerializer,
    OfferReadSerializer,
)
from marketplace.services.offer_service import OfferService


@extend_schema(
    tags=["Marketplace"],
    summary="Liste et création d'offres",
    description="GET : liste publique des offres (filtrable, paginée). POST : créer une offre (acheteur authentifié).",
    responses={200: OfferReadSerializer(many=True), 201: OfferReadSerializer},
)
class ListingOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        listing = get_object_or_404(Listing, pk=pk)

        serializer = OfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        offer = OfferService.create_offer(
            buyer=request.user,
            listing=listing,
            unit_amount=serializer.validated_data["unit_amount"],
            quantity=serializer.validated_data["quantity"],
            message=serializer.validated_data.get("message", ""),
        )

        return Response(
            OfferReadSerializer(offer).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Marketplace"],
    summary="Actions sur une offre",
    description="POST : Accepter, rejeter, annuler ou faire une contre-offre sur une offre (vendeur ou acheteur authentifié).",
    responses={200: OfferReadSerializer, 400: "Bad Request", 404: "Not Found"},
)
class OfferActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        offer = get_object_or_404(Offer, pk=pk)

        serializer = OfferActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]

        if action == "accept":
            offer = OfferService.accept_offer(
                offer=offer,
                user=request.user,
            )

        elif action == "reject":
            offer = OfferService.reject_offer(
                offer=offer,
                user=request.user,
            )

        elif action == "cancel":
            offer = OfferService.cancel_offer(
                offer=offer,
                user=request.user,
            )

        elif action == "counter":
            offer = OfferService.counter_offer(
                offer=offer,
                user=request.user,
                unit_amount=serializer.validated_data["unit_amount"],
                message=serializer.validated_data.get("message", ""),
            )

        return Response(OfferReadSerializer(offer).data)


@extend_schema(
    tags=["Marketplace"],
    summary="Liste des offres de l'utilisateur connecté",
    description="GET : Récupère la liste des offres faites par l'utilisateur connecté (acheteur).",
    responses={200: OfferReadSerializer(many=True)},
)
class MyOffersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = request.user.offers.select_related(
            "listing", "listing__store"
        ).order_by("-created_at")

        serializer = OfferReadSerializer(offers, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["Marketplace"],
    summary="Liste des offres reçues par le vendeur connecté",
    description="GET : Récupère la liste des offres reçues par le vendeur connecté (vendeur authentifié).",
    responses={200: OfferReadSerializer(many=True)},
)
class SellerOffersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = (
            Offer.objects.filter(listing__seller__user=request.user)
            .select_related("listing", "buyer")
            .order_by("-created_at")
        )

        serializer = OfferReadSerializer(offers, many=True)
        return Response(serializer.data)
